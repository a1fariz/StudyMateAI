"""
Generator service: generate summaries, quizzes, flashcards, and study plans
from documents using Gemini's structured output mode.
"""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.models.document import Document
from backend.services.pdf_processor import extract_text_from_pdf
from backend.services.gemini_service import GeminiService
from backend.schemas.features import (
    SummaryResponse,
    QuizResponse,
    FlashcardResponse,
    StudyPlanResponse,
)
from google.genai import types

settings = get_settings()
logger = logging.getLogger(__name__)

# Maximum characters to send to Gemini (safety cap ~100k words)
_MAX_CONTENT_CHARS = 400_000


async def _get_document_text(document_id: str, db: AsyncSession) -> tuple[str, str]:
    """
    Fetch a document, extract all text, and return a concatenated string and filename.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise ValueError("Document not found")
    if document.status != "processed":
        raise ValueError("Document is not processed yet")

    pages = extract_text_from_pdf(document.file_path)
    if not pages:
        raise ValueError("No text content could be extracted from the PDF")

    # Combine pages with page markers for better model context mapping
    full_text_parts = []
    for p in pages:
        full_text_parts.append(f"--- PAGE {p['page']} ---\n{p['content']}")

    full_text = "\n\n".join(full_text_parts)
    return full_text, document.original_filename


class GeneratorService:
    """Service utilizing Gemini structured output mode to generate learning aids."""

    @classmethod
    async def generate_summary(cls, document_id: str, db: AsyncSession) -> SummaryResponse:
        """Generate a 5-point summary of the document."""
        full_text, filename = await _get_document_text(document_id, db)
        client = GeminiService.get_client()

        prompt = (
            f"You are an expert study assistant. Analyze the following document text "
            f"and generate exactly 5 key summary points summarizing the main themes, "
            f"important facts, and concepts. Also suggest a suitable title for this summary.\n\n"
            f"Document Filename: {filename}\n\n"
            f"Document Content:\n{full_text[:_MAX_CONTENT_CHARS]}"
        )

        logger.info("Calling Gemini for structured summary generation")
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SummaryResponse,
                temperature=0.2,
            ),
        )

        # Gemini structured output returns the response as a JSON string matching the schema
        data = json.loads(response.text)
        return SummaryResponse(
            document_id=document_id,
            summary_points=data.get("summary_points", []),
            title=data.get("title", "Document Summary"),
        )

    @classmethod
    async def generate_quiz(
        cls, document_id: str, db: AsyncSession, num_questions: int = 10
    ) -> QuizResponse:
        """Generate multiple choice questions based on the document."""
        full_text, filename = await _get_document_text(document_id, db)
        client = GeminiService.get_client()

        prompt = (
            f"You are a teacher preparing an exam. Generate exactly {num_questions} "
            f"multiple choice questions based on the provided document content.\n"
            f"Each question must have exactly 4 choices, with 1 correct option index (0 to 3), "
            f"and a helpful explanation of why the correct option is right.\n\n"
            f"Document Content:\n{full_text[:_MAX_CONTENT_CHARS]}"
        )

        logger.info(f"Calling Gemini to generate {num_questions} quiz questions")
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuizResponse,
                temperature=0.4,
            ),
        )

        data = json.loads(response.text)
        return QuizResponse(
            document_id=document_id,
            questions=data.get("questions", []),
        )

    @classmethod
    async def generate_flashcards(cls, document_id: str, db: AsyncSession) -> FlashcardResponse:
        """Generate study flashcards (Question/Answer pairs) based on the document."""
        full_text, filename = await _get_document_text(document_id, db)
        client = GeminiService.get_client()

        prompt = (
            f"You are helping a student prepare flashcards. Create a set of 10 to 15 useful "
            f"Q&A flashcards highlighting the most important terms, dates, formulas, or "
            f"theories in the document.\n\n"
            f"Document Content:\n{full_text[:_MAX_CONTENT_CHARS]}"
        )

        logger.info("Calling Gemini to generate flashcards")
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FlashcardResponse,
                temperature=0.3,
            ),
        )

        data = json.loads(response.text)
        return FlashcardResponse(
            document_id=document_id,
            flashcards=data.get("flashcards", []),
        )

    @classmethod
    async def generate_study_plan(
        cls, document_id: str, db: AsyncSession, days: int = 7
    ) -> StudyPlanResponse:
        """Generate a study schedule based on the document."""
        full_text, filename = await _get_document_text(document_id, db)
        client = GeminiService.get_client()

        prompt = (
            f"You are a study coach. Create a structured {days}-day study plan to help "
            f"a student master the content in this document.\n"
            f"Break down the material logically across the {days} days, defining a daily topic "
            f"and a list of actionable tasks (e.g. read specific topics, practice questions, etc.).\n\n"
            f"Document Content:\n{full_text[:_MAX_CONTENT_CHARS]}"
        )

        logger.info(f"Calling Gemini to generate a {days}-day study plan")
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StudyPlanResponse,
                temperature=0.3,
            ),
        )

        data = json.loads(response.text)
        return StudyPlanResponse(
            document_id=document_id,
            days=data.get("days", []),
        )
