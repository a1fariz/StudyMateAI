"""
RAG Service: orchestrates the full Retrieval-Augmented Generation pipeline.

Flow:
  Question → Embed → Search ChromaDB → Load History → Gemini → Save Messages → Response
"""

import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.config import get_settings
from backend.models.conversation import Conversation, Message
from backend.services.embedding import EmbeddingService
from backend.services.vector_store import VectorStoreService
from backend.services.gemini_service import GeminiService

settings = get_settings()
logger = logging.getLogger(__name__)


def _extract_cited_pages(answer: str, context_chunks: list[dict]) -> list[dict]:
    """
    Extract source citations from the answer and context.

    Returns a list of source dicts:
    [{"page": 12, "content_preview": "..."}, ...]
    """
    sources = []
    seen_pages = set()

    # Extract [Page X] references from Gemini's answer
    page_refs = re.findall(r"\[Page\s+(\d+)\]", answer)

    # Map page numbers from context chunks
    page_chunk_map: dict[int, str] = {}
    for chunk in context_chunks:
        page = chunk.get("page_number", 0)
        content = chunk.get("content", "")
        if page not in page_chunk_map:
            page_chunk_map[page] = content[:150]  # preview

    # First: add pages explicitly cited by Gemini
    for page_str in page_refs:
        page = int(page_str)
        if page not in seen_pages:
            seen_pages.add(page)
            sources.append({
                "page": page,
                "content_preview": page_chunk_map.get(page, ""),
                "cited_in_answer": True,
            })

    # Then: add remaining context pages as supporting sources
    for chunk in context_chunks:
        page = chunk.get("page_number", 0)
        if page not in seen_pages:
            seen_pages.add(page)
            sources.append({
                "page": page,
                "content_preview": chunk.get("content", "")[:150],
                "cited_in_answer": False,
            })

    # Sort by page number
    sources.sort(key=lambda s: s["page"])
    return sources


async def _get_or_create_conversation(
    conversation_id: str | None,
    user_id: str,
    document_id: str | None,
    question: str,
    db: AsyncSession,
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation
        logger.warning(
            f"Conversation {conversation_id} not found, creating new one"
        )

    # Create new conversation with the question as title
    title = question[:80] + ("..." if len(question) > 80 else "")
    conversation = Conversation(
        title=title,
        user_id=user_id,
        document_id=document_id,
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    logger.info(f"Created conversation: {conversation.id}")
    return conversation


async def _load_chat_history(
    conversation_id: str,
    db: AsyncSession,
    limit: int | None = None,
) -> list[dict]:
    """Load recent messages from a conversation."""
    _limit = limit or settings.RAG_HISTORY_LIMIT

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(_limit)
    )
    messages = result.scalars().all()

    # Reverse to get chronological order
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(messages)
    ]
    return history


async def ask(
    question: str,
    user_id: str,
    db: AsyncSession,
    document_id: str | None = None,
    conversation_id: str | None = None,
) -> dict:
    """
    Full RAG pipeline: question → answer with sources.

    Args:
        question: The student's question.
        user_id: Current user's ID.
        db: Database session.
        document_id: Optional document to scope the search.
        conversation_id: Optional existing conversation to continue.

    Returns:
        {
            "answer": "...",
            "sources": [...],
            "conversation_id": "...",
            "message_id": "...",
        }
    """
    logger.info(f"RAG pipeline started — question: '{question[:60]}...'")

    # Step 1: Get or create conversation
    conversation = await _get_or_create_conversation(
        conversation_id, user_id, document_id, question, db
    )

    # Step 2: Embed the question
    logger.info("Step 1/5: Embedding question")
    query_embedding = EmbeddingService.embed_query(question)

    # Step 3: Retrieve relevant chunks from ChromaDB
    logger.info("Step 2/5: Searching vector store")
    context_chunks = VectorStoreService.search(
        query_embedding=query_embedding,
        document_id=document_id,
        top_k=settings.RAG_TOP_K,
    )
    logger.info(f"Retrieved {len(context_chunks)} chunks")

    # Step 4: Load conversation history
    logger.info("Step 3/5: Loading chat history")
    chat_history = await _load_chat_history(conversation.id, db)

    # Step 5: Generate answer with Gemini
    logger.info("Step 4/5: Generating answer with Gemini")
    answer = GeminiService.generate_answer(
        question=question,
        context_chunks=context_chunks,
        chat_history=chat_history,
    )

    # Step 6: Extract source citations
    logger.info("Step 5/5: Extracting citations")
    sources = _extract_cited_pages(answer, context_chunks)

    # Step 7: Save messages to database
    # Save user message
    user_message = Message(
        role="user",
        content=question,
        conversation_id=conversation.id,
    )
    db.add(user_message)

    # Save assistant message with sources
    assistant_message = Message(
        role="assistant",
        content=answer,
        sources=json.dumps(sources) if sources else None,
        conversation_id=conversation.id,
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    logger.info(
        f"✅ RAG complete — conversation: {conversation.id}, "
        f"sources: {len(sources)}, answer: {len(answer)} chars"
    )

    return {
        "answer": answer,
        "sources": sources,
        "conversation_id": conversation.id,
        "message_id": assistant_message.id,
    }
