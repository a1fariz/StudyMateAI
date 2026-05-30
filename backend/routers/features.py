"""
Features router: endpoints for generating study summaries, quizzes,
flashcards, study plans, and downloading PDF reports.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.routers.documents import _get_user_document
from backend.services.auth import get_current_user
from backend.services.generator_service import GeneratorService
from backend.services.pdf_exporter import generate_summary_pdf
from backend.schemas.features import (
    SummaryResponse,
    QuizResponse,
    FlashcardResponse,
    StudyPlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Smart Study Features"])


# ──────────────────────────────────────
# POST /{id}/summary
# ──────────────────────────────────────
@router.post("/{document_id}/summary", response_model=SummaryResponse)
async def get_summary(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a 5-point study summary from the document content using Gemini.
    """
    # Verify document ownership and processed status
    await _get_user_document(document_id, db, current_user)

    try:
        summary = await GeneratorService.generate_summary(document_id, db)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


# ──────────────────────────────────────
# POST /{id}/quiz
# ──────────────────────────────────────
@router.post("/{document_id}/quiz", response_model=QuizResponse)
async def get_quiz(
    document_id: str,
    num_questions: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate multiple choice study quiz questions based on the document content.
    """
    await _get_user_document(document_id, db, current_user)

    try:
        quiz = await GeneratorService.generate_quiz(document_id, db, num_questions)
        return quiz
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate quiz: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}",
        )


# ──────────────────────────────────────
# POST /{id}/flashcards
# ──────────────────────────────────────
@router.post("/{document_id}/flashcards", response_model=FlashcardResponse)
async def get_flashcards(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate study Q&A flashcards based on the document content.
    """
    await _get_user_document(document_id, db, current_user)

    try:
        flashcards = await GeneratorService.generate_flashcards(document_id, db)
        return flashcards
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate flashcards: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}",
        )


# ──────────────────────────────────────
# POST /{id}/study-plan
# ──────────────────────────────────────
@router.post("/{document_id}/study-plan", response_model=StudyPlanResponse)
async def get_study_plan(
    document_id: str,
    days: int = Query(7, ge=3, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a day-by-day study schedule to cover the material in the document.
    """
    await _get_user_document(document_id, db, current_user)

    try:
        plan = await GeneratorService.generate_study_plan(document_id, db, days)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate study plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study plan: {str(e)}",
        )


# ──────────────────────────────────────
# GET /{id}/export-summary (PDF Download)
# ──────────────────────────────────────
@router.get("/{document_id}/export-summary")
async def export_summary(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate and download a beautifully styled PDF containing the key summary points.
    """
    # 1. Fetch document (verifies ownership)
    doc = await _get_user_document(document_id, db, current_user)

    try:
        # 2. Generate summary points using the generator service
        summary = await GeneratorService.generate_summary(document_id, db)

        # 3. Generate PDF report binary stream
        pdf_buffer = generate_summary_pdf(
            filename=doc.original_filename,
            title=summary.title,
            summary_points=summary.summary_points,
        )

        headers = {
            "Content-Disposition": f'attachment; filename="summary_{document_id[:8]}.pdf"'
        }
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export PDF summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export PDF summary: {str(e)}",
        )
