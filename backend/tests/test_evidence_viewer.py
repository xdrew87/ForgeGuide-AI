"""
Evidence viewer — highlight search regression tests.
"""
import os
import pytest

DEMO_PDF = os.path.join(
    os.path.dirname(__file__), "..", "..", "demo-data",
    "MX400-Maintenance-Manual-DEMO.pdf"
)


class TestHighlightSearch:
    def test_finds_rects_for_real_chunk_substring(self):
        """A substring actually extracted from the demo PDF must be locatable."""
        from app.services.ingestion import _extract_text_from_pdf, _chunk_page_text
        from app.services.highlights import find_highlight_rects

        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found — run scripts/generate_demo_manual.py first")

        pages = _extract_text_from_pdf(DEMO_PDF)
        page_with_text = next(p for p in pages if len(p["text"]) > 200)
        chunks = _chunk_page_text(page_with_text["page"], page_with_text["text"])
        assert chunks, "Expected at least one chunk on the selected page"

        page_width, page_height, rects = find_highlight_rects(
            DEMO_PDF, page_with_text["page"], chunks[0]["text"]
        )
        assert page_width > 0 and page_height > 0
        assert len(rects) > 0

    def test_unmatchable_string_returns_empty_without_raising(self):
        from app.services.highlights import find_highlight_rects

        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")

        page_width, page_height, rects = find_highlight_rects(
            DEMO_PDF, 1, "zzz_this_text_does_not_exist_anywhere_zzz qux quux"
        )
        assert rects == []

    def test_out_of_range_page_returns_empty(self):
        from app.services.highlights import find_highlight_rects

        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")

        page_width, page_height, rects = find_highlight_rects(DEMO_PDF, 9999, "anything")
        assert rects == []
