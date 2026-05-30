"""
Text chunking service: split extracted PDF text into smaller,
overlapping chunks using LangChain's RecursiveCharacterTextSplitter.

Preserves page-number metadata so we can cite sources in Phase 3.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def chunk_document(
    pages: list[dict],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict]:
    """
    Split page-by-page text into overlapping chunks with metadata.

    Args:
        pages: Output from pdf_processor.extract_text_from_pdf()
               [{"page": 1, "content": "..."}, ...]
        chunk_size: Characters per chunk (default from settings).
        chunk_overlap: Overlap between chunks (default from settings).

    Returns:
        List of chunk dicts:
        [
            {
                "chunk_id": "doc_chunk_0",
                "content": "...",
                "page_number": 1,
                "chunk_index": 0,
                "word_count": 85,
            },
            ...
        ]
    """
    _chunk_size = chunk_size or settings.CHUNK_SIZE
    _chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_chunk_size,
        chunk_overlap=_chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []
    chunk_index = 0

    for page in pages:
        page_number = page["page"]
        page_text = page["content"]

        if not page_text.strip():
            continue

        # Split the page text into sub-chunks
        splits = splitter.split_text(page_text)

        for split_text in splits:
            chunks.append({
                "chunk_index": chunk_index,
                "content": split_text,
                "page_number": page_number,
                "word_count": len(split_text.split()),
            })
            chunk_index += 1

    logger.info(
        f"Chunked {len(pages)} pages into {len(chunks)} chunks "
        f"(size={_chunk_size}, overlap={_chunk_overlap})"
    )
    return chunks
