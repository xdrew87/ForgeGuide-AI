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


def _header_cells(table_markdown: str) -> list[str]:
    first = next((ln for ln in table_markdown.splitlines() if ln.strip().startswith("|")), "")
    return [_normalize(c) for c in first.strip().strip("|").split("|")]


def find_table_highlight_rects(
    pdf_path: str, page_number: int, table_markdown: str, quote: str = ""
) -> tuple[float, float, list[tuple[float, float, float, float]]]:
    """
    Highlight for a table citation. Text search can't work on the synthesized
    markdown, so locate the table on the page by its header row, then:
      - if the LLM's quoted text is found inside the table, highlight the whole
        table ROW(s) containing it (e.g. the E09 row of a fault-code table);
      - otherwise highlight the entire table.
    Returns an empty rects list if no matching table is found (caller falls
    back to showing the plain page).
    """
    doc = fitz.open(pdf_path)
    try:
        if page_number < 1 or page_number > len(doc):
            return 0.0, 0.0, []
        page = doc[page_number - 1]
        page_width, page_height = page.rect.width, page.rect.height

        header = _header_cells(table_markdown)
        table = None
        for tab in page.find_tables().tables:
            extracted = tab.extract()
            if extracted and [_normalize(str(c or "")) for c in extracted[0]] == header:
                table = tab
                break
        if table is None:
            return page_width, page_height, []

        tx0, ty0, tx1, ty1 = table.bbox
        table_rect = fitz.Rect(table.bbox)

        norm_quote = _normalize(quote.replace("|", " "))
        # A quote that is just the header row (small models do this) identifies
        # no particular row — treat it as "no quote" so the whole table shows
        # instead of only the header being highlighted.
        if norm_quote and norm_quote.lower() in " ".join(header).lower():
            norm_quote = ""
        hit_rects = []
        if norm_quote:
            for attempt in (norm_quote, " ".join(norm_quote.split()[:6])):
                hit_rects = [r for r in page.search_for(attempt) if r.intersects(table_rect)]
                if hit_rects:
                    break

        if hit_rects:
            # Use each hit's center point, not rect overlap: text boxes can
            # overflow their cell slightly and would bleed into adjacent rows.
            centers = [fitz.Point((h.x0 + h.x1) / 2, (h.y0 + h.y1) / 2) for h in hit_rects]
            rows = []
            for row in table.rows:
                row_rect = fitz.Rect(row.bbox)
                if any(row_rect.contains(c) for c in centers):
                    rows.append((row_rect.x0, row_rect.y0, row_rect.x1, row_rect.y1))
            if rows:
                return page_width, page_height, rows

        return page_width, page_height, [(tx0, ty0, tx1, ty1)]
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
