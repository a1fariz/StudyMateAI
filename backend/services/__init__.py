"""
Services for StudyMate AI.
"""

from backend.services.auth import hash_password, verify_password, create_access_token, get_current_user
from backend.services.chunking import chunk_document
from backend.services.embedding import EmbeddingService
from backend.services.pdf_processor import extract_text_from_pdf, get_pdf_page_count
from backend.services.vector_store import VectorStoreService
from backend.services.gemini_service import GeminiService
from backend.services import rag_service
from backend.services.generator_service import GeneratorService
from backend.services.pdf_exporter import generate_summary_pdf

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_current_user",
    "chunk_document",
    "EmbeddingService",
    "extract_text_from_pdf",
    "get_pdf_page_count",
    "VectorStoreService",
    "GeminiService",
    "rag_service",
    "GeneratorService",
    "generate_summary_pdf",
]
