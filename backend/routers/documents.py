"""
Document router: upload PDF, list documents, get document details,
parse/extract text, delete document.
"""

import uuid
import os
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.database import get_db
from backend.models.user import User
from backend.models.document import Document
from backend.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentParseResponse,
    PageContent,
)
from backend.services.auth import get_current_user
from backend.services.pdf_processor import extract_text_from_pdf, get_pdf_page_count
from backend.services.vector_store import VectorStoreService

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


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
# POST /upload — Upload PDF
# ──────────────────────────────────────
@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF document. File is saved and metadata is stored."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit",
        )

    # Create upload directory per user
    upload_dir = Path(settings.UPLOAD_DIR) / current_user.id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file with unique name
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.pdf"
    file_path = upload_dir / filename

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        )

    # Get page count
    page_count = get_pdf_page_count(str(file_path))

    # Save metadata to database
    document = Document(
        id=file_id,
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        page_count=page_count,
        owner_id=current_user.id,
        status="uploaded",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    logger.info(
        f"User {current_user.username} uploaded: {file.filename} "
        f"({page_count} pages, {file_size / 1024:.1f} KB)"
    )
    return document


# ──────────────────────────────────────
# GET / — List documents
# ──────────────────────────────────────
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents for the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()
    return DocumentListResponse(documents=documents, total=len(documents))


# ──────────────────────────────────────
# GET /{id} — Get document details
# ──────────────────────────────────────
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific document's details."""
    return await _get_user_document(document_id, db, current_user)


# ──────────────────────────────────────
# POST /{id}/parse — Extract text from PDF
# ──────────────────────────────────────
@router.post("/{document_id}/parse", response_model=DocumentParseResponse)
async def parse_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract text from an uploaded PDF document.

    Returns page-by-page text content with word counts.
    Updates document status to 'processed' on success.
    """
    document = await _get_user_document(document_id, db, current_user)

    # Update status to processing
    document.status = "processing"
    await db.flush()

    try:
        # Extract text from PDF
        raw_pages = extract_text_from_pdf(document.file_path)

        # Build structured response
        pages = []
        total_words = 0
        for p in raw_pages:
            word_count = len(p["content"].split())
            total_words += word_count
            pages.append(PageContent(
                page=p["page"],
                content=p["content"],
                word_count=word_count,
            ))

        # Update document status
        document.status = "processed"
        await db.flush()

        logger.info(
            f"Parsed document {document.original_filename}: "
            f"{len(pages)} pages, {total_words} words"
        )

        return DocumentParseResponse(
            document_id=document.id,
            filename=document.original_filename,
            total_pages=document.page_count,
            pages_with_text=len(pages),
            total_words=total_words,
            pages=pages,
            status="processed",
        )

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
        logger.error(f"Failed to parse document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from PDF: {str(e)}",
        )


# ──────────────────────────────────────
# DELETE /{id} — Delete document
# ──────────────────────────────────────
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document, its file from disk, and its vectors from ChromaDB."""
    document = await _get_user_document(document_id, db, current_user)

    # Delete vectors from ChromaDB
    try:
        VectorStoreService.delete_document(document_id)
    except Exception as e:
        logger.warning(f"Failed to delete vectors for {document_id}: {e}")

    # Delete file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            logger.info(f"Deleted file: {document.file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file {document.file_path}: {e}")

    # Delete from database
    await db.delete(document)

