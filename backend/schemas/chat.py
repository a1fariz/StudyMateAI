"""
Chat schemas for conversations and messages.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """Request to ask a question via the RAG pipeline."""
    question: str = Field(..., min_length=1, max_length=2000, description="User question")
    document_id: str | None = Field(None, description="Optional document context")
    conversation_id: str | None = Field(None, description="Continue existing conversation")


class SourceItem(BaseModel):
    """A single source citation."""
    page: int
    content_preview: str = ""
    cited_in_answer: bool = False


class MessageResponse(BaseModel):
    """A single message in a conversation."""
    id: str
    role: str
    content: str
    sources: list[SourceItem] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Response from the RAG pipeline."""
    answer: str
    sources: list[SourceItem] | None = None
    conversation_id: str
    message_id: str


class ConversationResponse(BaseModel):
    """Summary of a conversation (for lists)."""
    id: str
    title: str
    document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""
    conversations: list[ConversationResponse]
    total: int


class ConversationDetailResponse(BaseModel):
    """A conversation with all its messages."""
    id: str
    title: str
    document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]
