"""
Chat router: RAG chatbot endpoint and conversation history management.

Endpoints:
  POST   /chat                      — Ask a question, get a RAG answer
  GET    /conversations              — List user's conversations
  GET    /conversations/{id}         — Get conversation with messages
  DELETE /conversations/{id}         — Delete a conversation
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.models.user import User
from backend.models.document import Document
from backend.models.conversation import Conversation, Message
from backend.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceItem,
    MessageResponse,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
)
from backend.services.auth import get_current_user
from backend.services import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# ──────────────────────────────────────
# POST /chat — RAG Q&A
# ──────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ask a question and get an AI-generated answer with source citations.

    The full RAG pipeline:
    1. Embed the question
    2. Retrieve relevant chunks from ChromaDB
    3. Load conversation history
    4. Generate answer with Gemini
    5. Save messages and return response

    Optionally provide `document_id` to scope search to a specific document,
    and `conversation_id` to continue an existing conversation.
    """
    # Validate document ownership if specified
    if req.document_id:
        result = await db.execute(
            select(Document).where(
                Document.id == req.document_id,
                Document.owner_id == current_user.id,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.status != "processed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Document has not been processed yet. "
                    "Call POST /api/v1/documents/{id}/process first."
                ),
            )

    # Validate conversation ownership if specified
    if req.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == req.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    try:
        # Run the RAG pipeline
        result = await rag_service.ask(
            question=req.question,
            user_id=current_user.id,
            db=db,
            document_id=req.document_id,
            conversation_id=req.conversation_id,
        )

        # Convert sources to schema objects
        sources = None
        if result.get("sources"):
            sources = [SourceItem(**s) for s in result["sources"]]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
        )

    except RuntimeError as e:
        # Gemini API key not configured
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}",
        )


# ──────────────────────────────────────
# GET /conversations — List conversations
# ──────────────────────────────────────
@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all conversations for the current user, newest first."""
    # Get conversations with message counts
    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )
    rows = result.all()

    conversations = []
    for conv, msg_count in rows:
        conversations.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                document_id=conv.document_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
            )
        )

    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations),
    )


# ──────────────────────────────────────
# GET /conversations/{id} — Get conversation detail
# ──────────────────────────────────────
@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Load messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    # Build message responses with parsed sources
    message_responses = []
    for msg in messages:
        sources = None
        if msg.sources:
            try:
                sources = [SourceItem(**s) for s in json.loads(msg.sources)]
            except (json.JSONDecodeError, TypeError):
                sources = None

        message_responses.append(
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=sources,
                created_at=msg.created_at,
            )
        )

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        document_id=conversation.document_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses,
    )


# ──────────────────────────────────────
# DELETE /conversations/{id}
# ──────────────────────────────────────
@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conversation)
    logger.info(f"Deleted conversation {conversation_id}")
