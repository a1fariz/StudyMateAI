"""
PDF processing service: extract text from uploaded PDFs using PyMuPDF.
"""

import fitz  # PyMuPDF
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF file page by page.

    Returns:
        List of dicts with page number and content:
        [{"page": 1, "content": "..."}, ...]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    pages = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:  # Skip empty pages
                pages.append({
                    "page": page_num + 1,
                    "content": text,
                })
        doc.close()
        logger.info(f"Extracted text from {len(pages)} pages of {path.name}")
    except Exception as e:
        logger.error(f"Failed to extract text from {path.name}: {e}")
        raise

    return pages


def get_pdf_page_count(file_path: str) -> int:
    """Get the total number of pages in a PDF."""
    try:
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0
