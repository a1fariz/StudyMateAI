"""
Pydantic schemas for request/response validation.
"""

from backend.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
)
from backend.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
)
from backend.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceItem,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
    MessageResponse,
)
from backend.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    ProcessDocumentResponse,
)
from backend.schemas.features import (
    SummaryResponse,
    QuizResponse,
    QuizQuestion,
    FlashcardResponse,
    FlashcardItem,
    StudyPlanResponse,
    StudyPlanDay,
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "Token", "TokenData",
    "DocumentResponse", "DocumentListResponse",
    "ChatRequest", "ChatResponse", "SourceItem",
    "ConversationResponse", "ConversationListResponse",
    "ConversationDetailResponse", "MessageResponse",
    "SearchRequest", "SearchResponse", "SearchResultItem", "ProcessDocumentResponse",
    "SummaryResponse", "QuizResponse", "QuizQuestion", "FlashcardResponse",
    "FlashcardItem", "StudyPlanResponse", "StudyPlanDay",
]
