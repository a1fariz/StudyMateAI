"""
Vector store service: ChromaDB wrapper for storing and retrieving
document chunk embeddings.

Uses persistent storage so vectors survive server restarts.
"""

from __future__ import annotations

import logging
import chromadb

from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorStoreService:
    """Singleton wrapper around a ChromaDB persistent collection."""

    _client: chromadb.PersistentClient | None = None
    _collection: chromadb.Collection | None = None

    @classmethod
    def get_collection(cls) -> chromadb.Collection:
        """
        Get or create the ChromaDB collection.
        Uses persistent storage at CHROMA_PERSIST_DIR.
        """
        if cls._collection is None:
            logger.info(
                f"Initializing ChromaDB at: {settings.CHROMA_PERSIST_DIR}"
            )
            cls._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
            )
            cls._collection = cls._client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},  # cosine similarity
            )
            logger.info(
                f"✅ ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' "
                f"ready — {cls._collection.count()} existing vectors"
            )
        return cls._collection

    @classmethod
    def add_document_chunks(
        cls,
        document_id: str,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> int:
        """
        Store document chunks and their embeddings in ChromaDB.

        Args:
            document_id: UUID of the document.
            chunks: List of chunk dicts from chunking service.
            embeddings: Corresponding embedding vectors.

        Returns:
            Number of chunks stored.
        """
        collection = cls.get_collection()

        ids = [f"{document_id}_chunk_{c['chunk_index']}" for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "page_number": c["page_number"],
                "chunk_index": c["chunk_index"],
                "word_count": c["word_count"],
            }
            for c in chunks
        ]

        # ChromaDB upsert — safe to re-run on the same document
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            f"Stored {len(chunks)} chunks for document {document_id} "
            f"in ChromaDB (total vectors: {collection.count()})"
        )
        return len(chunks)

    @classmethod
    def search(
        cls,
        query_embedding: list[float],
        document_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Perform similarity search in the vector store.

        Args:
            query_embedding: Query vector from EmbeddingService.
            document_id: Optional — restrict search to a specific document.
            top_k: Number of results to return.

        Returns:
            List of result dicts with content, metadata, and distance score.
        """
        collection = cls.get_collection()

        # Build optional filter
        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Flatten ChromaDB's nested response format
        search_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns cosine distance; convert to similarity score
                distance = results["distances"][0][i]
                similarity = 1 - distance  # cosine distance → similarity

                search_results.append({
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i],
                    "page_number": results["metadatas"][0][i]["page_number"],
                    "chunk_index": results["metadatas"][0][i]["chunk_index"],
                    "document_id": results["metadatas"][0][i]["document_id"],
                    "word_count": results["metadatas"][0][i]["word_count"],
                    "score": round(similarity, 4),
                })

        logger.info(
            f"Search returned {len(search_results)} results "
            f"(top_k={top_k}, doc_filter={'yes' if document_id else 'no'})"
        )
        return search_results

    @classmethod
    def delete_document(cls, document_id: str) -> int:
        """
        Remove all chunks for a specific document from the vector store.

        Args:
            document_id: UUID of the document to remove.

        Returns:
            Number of chunks deleted.
        """
        collection = cls.get_collection()

        # Get existing chunks for this document
        existing = collection.get(
            where={"document_id": document_id},
            include=[],
        )
        count = len(existing["ids"]) if existing["ids"] else 0

        if count > 0:
            collection.delete(
                where={"document_id": document_id},
            )
            logger.info(
                f"Deleted {count} chunks for document {document_id} from ChromaDB"
            )
        else:
            logger.info(f"No chunks found for document {document_id} in ChromaDB")

        return count

    @classmethod
    def get_document_chunk_count(cls, document_id: str) -> int:
        """Get the number of stored chunks for a document."""
        collection = cls.get_collection()
        existing = collection.get(
            where={"document_id": document_id},
            include=[],
        )
        return len(existing["ids"]) if existing["ids"] else 0
