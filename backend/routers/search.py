"""
Search router: process documents (chunk + embed + store) and
perform semantic similarity search.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.database import get_db
from backend.models.user import User
from backend.models.document import Document
from backend.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    ProcessDocumentResponse,
)
from backend.services.auth import get_current_user
from backend.services.pdf_processor import extract_text_from_pdf
from backend.services.chunking import chunk_document
from backend.services.embedding import EmbeddingService
from backend.services.vector_store import VectorStoreService

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Search"])


# ──────────────────────────────────────
# Helper: ownership check
# ──────────────────────────────────────
async def _get_user_document(
    document_id: str,
    db: AsyncSession,
    current_user: User,
) -> Document:
    """Fetch a document owned by the current user or raise 404."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


# ──────────────────────────────────────
# POST /documents/{id}/process
# Full pipeline: PDF → Chunks → Embeddings → ChromaDB
# ──────────────────────────────────────
@router.post(
    "/documents/{document_id}/process",
    response_model=ProcessDocumentResponse,
)
async def process_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process a document through the full AI pipeline:
    1. Extract text from PDF (PyMuPDF)
    2. Chunk text (RecursiveCharacterTextSplitter)
    3. Generate embeddings (all-MiniLM-L6-v2)
    4. Store in vector database (ChromaDB)

    This must be called before semantic search works on a document.
    Safe to re-run — existing chunks are upserted (replaced).
    """
    document = await _get_user_document(document_id, db, current_user)

    # Update status
    document.status = "processing"
    await db.flush()

    try:
        # Step 1: Extract text from PDF
        logger.info(f"Step 1/4: Extracting text from {document.original_filename}")
        pages = extract_text_from_pdf(document.file_path)

        if not pages:
            document.status = "failed"
            document.error_message = "No text content found in PDF"
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text content found in the PDF. The file may be image-based.",
            )

        # Step 2: Chunk the text
        logger.info(f"Step 2/4: Chunking text into segments")
        chunks = chunk_document(pages)

        if not chunks:
            document.status = "failed"
            document.error_message = "Text chunking produced no results"
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Text chunking produced no results.",
            )

        # Step 3: Generate embeddings
        logger.info(f"Step 3/4: Generating embeddings for {len(chunks)} chunks")
        texts = [c["content"] for c in chunks]
        embeddings = EmbeddingService.embed_texts(texts)

        # Step 4: Store in ChromaDB
        logger.info(f"Step 4/4: Storing vectors in ChromaDB")
        stored_count = VectorStoreService.add_document_chunks(
            document_id=document.id,
            chunks=chunks,
            embeddings=embeddings,
        )

        # Calculate stats
        total_words = sum(c["word_count"] for c in chunks)

        # Update document status
        document.status = "processed"
        document.error_message = None
        await db.flush()

        logger.info(
            f"✅ Document processed: {document.original_filename} — "
            f"{len(pages)} pages, {stored_count} chunks, {total_words} words"
        )

        return ProcessDocumentResponse(
            document_id=document.id,
            filename=document.original_filename,
            total_chunks=stored_count,
            total_pages=len(pages),
            total_words=total_words,
            status="processed",
            message=(
                f"Successfully processed '{document.original_filename}': "
                f"{stored_count} chunks from {len(pages)} pages "
                f"({total_words} words). Ready for semantic search."
            ),
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except FileNotFoundError:
        document.status = "failed"
        document.error_message = "PDF file not found on disk"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk. It may have been deleted.",
        )
    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)
        await db.flush()
        logger.error(f"Failed to process document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


# ──────────────────────────────────────
# POST /search — Semantic similarity search
# ──────────────────────────────────────
@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    search_req: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search across processed documents using semantic similarity.

    Converts the query into an embedding, then finds the most similar
    document chunks in ChromaDB. Optionally filter by document_id.

    Returns ranked results with content, page numbers, and similarity scores.
    """
    # Validate document ownership if document_id is provided
    if search_req.document_id:
        await _get_user_document(search_req.document_id, db, current_user)

        # Check if document has been processed
        chunk_count = VectorStoreService.get_document_chunk_count(
            search_req.document_id
        )
        if chunk_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This document has not been processed yet. "
                    "Call POST /api/v1/documents/{id}/process first."
                ),
            )

    # Generate query embedding
    query_embedding = EmbeddingService.embed_query(search_req.query)

    # Search ChromaDB
    raw_results = VectorStoreService.search(
        query_embedding=query_embedding,
        document_id=search_req.document_id,
        top_k=search_req.top_k,
    )

    # Verify document ownership for all results (security check)
    # when no document_id filter was applied
    if not search_req.document_id:
        user_doc_result = await db.execute(
            select(Document.id).where(Document.owner_id == current_user.id)
        )
        user_doc_ids = {row[0] for row in user_doc_result.fetchall()}
        raw_results = [r for r in raw_results if r["document_id"] in user_doc_ids]

    # Build response
    results = [
        SearchResultItem(
            content=r["content"],
            page_number=r["page_number"],
            chunk_index=r["chunk_index"],
            score=r["score"],
            document_id=r["document_id"],
            word_count=r["word_count"],
        )
        for r in raw_results
    ]

    return SearchResponse(
        query=search_req.query,
        results=results,
        total_results=len(results),
    )
