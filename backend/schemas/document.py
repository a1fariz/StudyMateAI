"""
Document schemas for upload responses.
"""

from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    page_count: int
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class PageContent(BaseModel):
    """Extracted text content from a single PDF page."""
    page: int
    content: str
    word_count: int = 0


class DocumentParseResponse(BaseModel):
    """Response for PDF text extraction."""
    document_id: str
    filename: str
    total_pages: int
    pages_with_text: int
    total_words: int
    pages: list[PageContent]
    status: str
