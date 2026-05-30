"""
Gemini service: wrapper around Google Generative AI SDK.

Builds a RAG prompt from retrieved chunks and conversation history,
then calls Gemini to generate a grounded answer with source citations.
"""

import logging
from google import genai
from google.genai import types

from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# ──────────────────────────────────────
# RAG System Prompt
# ──────────────────────────────────────
SYSTEM_PROMPT = """\
You are StudyMate AI, an intelligent study assistant. Your job is to help
students understand their study materials by answering questions accurately.

RULES:
1. Answer ONLY based on the provided context below. Do NOT use outside knowledge.
2. When you reference information, cite the source page using [Page X] format.
3. If the context does not contain enough information to answer, say:
   "I don't have enough information in the provided documents to answer this question."
4. Be concise but thorough. Use bullet points or numbered lists when helpful.
5. If the student asks a follow-up, use the conversation history for continuity.
"""

CONTEXT_TEMPLATE = """\
CONTEXT FROM DOCUMENTS:
{context}

CONVERSATION HISTORY:
{history}

STUDENT QUESTION:
{question}
"""


class GeminiService:
    """Singleton wrapper around the Google GenAI client."""

    _client: genai.Client | None = None

    @classmethod
    def get_client(cls) -> genai.Client:
        """Lazy-initialize the Gemini client."""
        if cls._client is None:
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured. "
                    "Set it in your .env file. Get a free key at https://aistudio.google.com/apikey"
                )
            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info(f"✅ Gemini client initialized (model: {settings.GEMINI_MODEL})")
        return cls._client

    @classmethod
    def generate_answer(
        cls,
        question: str,
        context_chunks: list[dict],
        chat_history: list[dict] | None = None,
    ) -> str:
        """
        Generate a RAG answer using Gemini.

        Args:
            question: The student's question.
            context_chunks: Retrieved chunks from ChromaDB, each with
                            'content', 'page_number', 'score'.
            chat_history: Optional list of past messages
                          [{"role": "user", "content": "..."}, ...]

        Returns:
            The generated answer string with [Page X] citations.
        """
        client = cls.get_client()

        # Build context string with page markers
        if context_chunks:
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                page = chunk.get("page_number", "?")
                content = chunk.get("content", "")
                context_parts.append(f"[Page {page}] (Chunk {i}):\n{content}")
            context_str = "\n\n".join(context_parts)
        else:
            context_str = "(No relevant context found in documents)"

        # Build history string
        if chat_history:
            history_parts = []
            for msg in chat_history:
                role = "Student" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_str = "\n".join(history_parts)
        else:
            history_str = "(No previous conversation)"

        # Build the full prompt
        user_prompt = CONTEXT_TEMPLATE.format(
            context=context_str,
            history=history_str,
            question=question,
        )

        logger.info(
            f"Calling Gemini ({settings.GEMINI_MODEL}) — "
            f"{len(context_chunks)} chunks, "
            f"{len(chat_history or [])} history messages"
        )

        # Call Gemini API
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
            ),
        )

        answer = response.text.strip()
        logger.info(f"Gemini response: {len(answer)} chars")
        return answer
