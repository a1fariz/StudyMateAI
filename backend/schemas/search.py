"""
Search schemas for semantic search request/response validation.
"""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for semantic search."""
    query: str = Field(
        ..., min_length=1, max_length=2000, description="Search query"
    )
    document_id: str | None = Field(
        None, description="Optional: restrict search to a specific document"
    )
    top_k: int = Field(
        5, ge=1, le=20, description="Number of results to return"
    )


class SearchResultItem(BaseModel):
    """A single search result with content and metadata."""
    content: str
    page_number: int
    chunk_index: int
    score: float
    document_id: str
    word_count: int = 0


class SearchResponse(BaseModel):
    """Response for semantic search."""
    query: str
    results: list[SearchResultItem]
    total_results: int


class ProcessDocumentResponse(BaseModel):
    """Response after processing a document through the AI pipeline."""
    document_id: str
    filename: str
    total_chunks: int
    total_pages: int
    total_words: int
    status: str
    message: str
