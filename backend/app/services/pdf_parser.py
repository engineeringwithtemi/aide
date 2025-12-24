"""PDF parsing service using PyMuPDF (pymupdf).

Extracts chapters and text content from PDF files.
"""

import pymupdf  # PyMuPDF
from typing import List
from dataclasses import dataclass
from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Chapter:
    """Chapter/section extracted from PDF."""
    id: str
    title: str
    start_page: int
    end_page: int
    text: str


async def extract_chapters(file_content: bytes) -> List[Chapter]:
    """Extract chapters from PDF content.

    Strategy:
    1. Try table of contents (TOC) first
    2. Fall back to heading detection (font size/style)
    3. Fall back to "Chapter N" pattern matching
    4. Fall back to page ranges if no structure found

    Args:
        file_content: PDF file bytes

    Returns:
        List of Chapter objects

    Raises:
        ValueError: If PDF is corrupt, encrypted, or empty
    """
    try:
        # Open PDF from bytes
        doc = pymupdf.open(stream=file_content, filetype="pdf")

        if doc.is_encrypted:
            raise ValueError("PDF is encrypted. Please provide an unencrypted version.")

        if doc.page_count == 0:
            raise ValueError("PDF has no pages.")

        logger.info(f"Parsing PDF with {doc.page_count} pages")

        # Try TOC first
        chapters = _extract_from_toc(doc)
        if chapters:
            logger.info(f"Extracted {len(chapters)} chapters from TOC")
            return chapters

        # Try heading detection
        chapters = _extract_from_headings(doc)
        if chapters:
            logger.info(f"Extracted {len(chapters)} chapters from headings")
            return chapters

        # Try pattern matching
        chapters = _extract_from_patterns(doc)
        if chapters:
            logger.info(f"Extracted {len(chapters)} chapters from patterns")
            return chapters

        # Fallback: divide into page ranges
        chapters = _extract_page_ranges(doc)
        logger.info(f"Using {len(chapters)} page range divisions")
        return chapters

    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    finally:
        if 'doc' in locals():
            doc.close()


def _extract_from_toc(doc: pymupdf.Document) -> List[Chapter]:
    """Extract chapters from PDF table of contents."""
    toc = doc.get_toc()
    if not toc:
        return []

    chapters = []
    for i, (level, title, page_num) in enumerate(toc):
        # Only use top-level entries (level 1)
        if level != 1:
            continue

        start_page = page_num - 1  # pymupdf uses 1-based page numbers

        # Find end page (start of next chapter or end of doc)
        end_page = doc.page_count - 1
        for j in range(i + 1, len(toc)):
            if toc[j][0] == 1:  # Next top-level entry
                end_page = toc[j][2] - 2
                break

        # Extract text from pages
        text = _extract_text_range(doc, start_page, end_page)

        chapters.append(Chapter(
            id=f"ch_{i+1}",
            title=title,
            start_page=start_page,
            end_page=end_page,
            text=text
        ))

    return chapters


def _extract_from_headings(doc: pymupdf.Document) -> List[Chapter]:
    """Detect chapters by analyzing font sizes and styles."""
    # TODO: Implement heading detection via font analysis
    # This is complex - for MVP, return empty to fall through to patterns
    return []


def _extract_from_patterns(doc: pymupdf.Document) -> List[Chapter]:
    """Find chapters by matching patterns like 'Chapter 1', 'Section 1', etc."""
    import re

    chapter_pattern = re.compile(r'^(Chapter|CHAPTER|Section|SECTION)\s+(\d+)', re.MULTILINE)
    chapters = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()

        match = chapter_pattern.search(text)
        if match:
            title = match.group(0)  # "Chapter 1"

            # Find end page (next chapter or end of doc)
            end_page = doc.page_count - 1
            for next_page_num in range(page_num + 1, doc.page_count):
                next_text = doc[next_page_num].get_text()
                if chapter_pattern.search(next_text):
                    end_page = next_page_num - 1
                    break

            text_content = _extract_text_range(doc, page_num, end_page)

            chapters.append(Chapter(
                id=f"ch_{len(chapters)+1}",
                title=title,
                start_page=page_num,
                end_page=end_page,
                text=text_content
            ))

    return chapters


def _extract_page_ranges(doc: pymupdf.Document) -> List[Chapter]:
    """Fallback: divide PDF into equal page ranges."""
    pages_per_chapter = 10
    chapters = []

    for i in range(0, doc.page_count, pages_per_chapter):
        start_page = i
        end_page = min(i + pages_per_chapter - 1, doc.page_count - 1)

        text = _extract_text_range(doc, start_page, end_page)

        chapters.append(Chapter(
            id=f"section_{len(chapters)+1}",
            title=f"Pages {start_page+1}-{end_page+1}",
            start_page=start_page,
            end_page=end_page,
            text=text
        ))

    return chapters


def _extract_text_range(doc: pymupdf.Document, start_page: int, end_page: int) -> str:
    """Extract text from page range."""
    texts = []
    for page_num in range(start_page, end_page + 1):
        page = doc[page_num]
        text = page.get_text()
        texts.append(text)

    return "\n\n".join(texts)


async def extract_text(file_content: bytes) -> str:
    """Extract all text from PDF (simpler alternative to chapters).

    Args:
        file_content: PDF file bytes

    Returns:
        Full text content
    """
    doc = pymupdf.open(stream=file_content, filetype="pdf")

    try:
        texts = []
        for page in doc:
            texts.append(page.get_text())
        return "\n\n".join(texts)
    finally:
        doc.close()