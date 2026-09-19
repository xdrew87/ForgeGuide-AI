"""
Evidence-viewer support: locate a citation's passage on its source PDF page
so the frontend can render a highlight overlay on the rendered page image.

Highlighting is computed at request time via PyMuPDF's search_for() against
the stored PDF — no bbox is persisted at ingestion time. Chunk text is a
direct substring of the page's extracted text (see ingestion.py), so
search_for() reliably locates it. Validated against the real demo PDF
(12/12 chunks matched on the first attempt).
"""
import logging

import pymupdf as fitz

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    return " ".join(text.split())


def find_highlight_rects(
    pdf_path: str, page_number: int, search_text: str
) -> tuple[float, float, list[tuple[float, float, float, float]]]:
    """
    Returns (page_width, page_height, rects) in PDF point units.

    Fallback chain — each a smaller prefix of the normalized search text —
    handles cases where the full chunk text doesn't match verbatim (e.g.
    minor whitespace/hyphenation differences). An empty rects list is the
    designed graceful-degradation outcome, not an error: it's expected for
    OCR'd pages (search_for only sees the embedded text layer, which OCR
    pages lack) and for table chunks (synthesized markdown, never literally
    on the page). Callers should render the whole page with no overlay in
    that case.
    """
    doc = fitz.open(pdf_path)
    try:
        if page_number < 1 or page_number > len(doc):
            return 0.0, 0.0, []

        page = doc[page_number - 1]
        page_width, page_height = page.rect.width, page.rect.height

        normalized = _normalize(search_text)
        words = normalized.split()
        attempts = [normalized, " ".join(words[:12]), " ".join(words[:6])]

        for attempt in attempts:
            if not attempt:
                continue
            rects = page.search_for(attempt)
            if rects:
                return (
                    page_width,
                    page_height,
                    [(r.x0, r.y0, r.x1, r.y1) for r in rects],
                )

        return page_width, page_height, []
    finally:
        doc.close()


def render_page_image(pdf_path: str, page_number: int, scale: float = 2.0) -> bytes | None:
    """Render a page to PNG bytes. Same fitz pixmap pattern as ingestion.py::_ocr_page."""
    doc = fitz.open(pdf_path)
    try:
        if page_number < 1 or page_number > len(doc):
            return None
        page = doc[page_number - 1]
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")
    finally:
        doc.close()
