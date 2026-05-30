"""
Schemas for smart generator features.
"""

from pydantic import BaseModel, Field


# ──────────────────────────────────────
# Summary Schemas
# ──────────────────────────────────────
class SummaryResponse(BaseModel):
    document_id: str
    summary_points: list[str] = Field(..., description="5 key summary points from the document")
    title: str = Field(..., description="Title or topic of the summarized content")


# ──────────────────────────────────────
# Quiz Schemas
# ──────────────────────────────────────
class QuizQuestion(BaseModel):
    question: str = Field(..., description="The multiple choice question")
    options: list[str] = Field(..., description="Exactly 4 options")
    correct_option: int = Field(..., description="Index of the correct option (0-3)")
    explanation: str = Field(..., description="Explanation of why the option is correct")


class QuizResponse(BaseModel):
    document_id: str
    questions: list[QuizQuestion] = Field(..., description="List of generated questions")


# ──────────────────────────────────────
# Flashcard Schemas
# ──────────────────────────────────────
class FlashcardItem(BaseModel):
    question: str = Field(..., description="Question on the front of the flashcard")
    answer: str = Field(..., description="Answer on the back of the flashcard")


class FlashcardResponse(BaseModel):
    document_id: str
    flashcards: list[FlashcardItem] = Field(..., description="Generated study flashcards")


# ──────────────────────────────────────
# Study Plan Schemas
# ──────────────────────────────────────
class StudyPlanDay(BaseModel):
    day: int = Field(..., description="Day number (e.g. 1)")
    topic: str = Field(..., description="Key topic or focus for the day")
    tasks: list[str] = Field(..., description="Daily practice tasks, readings, or activities")


class StudyPlanResponse(BaseModel):
    document_id: str
    days: list[StudyPlanDay] = Field(..., description="Structured daily study plan")
