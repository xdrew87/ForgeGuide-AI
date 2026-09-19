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

    def _fault_table_markdown(self):
        from app.services.ingestion import _extract_text_from_pdf, _table_to_markdown
        pages = _extract_text_from_pdf(DEMO_PDF)
        fault = next(t for p in pages for t in p["tables"] if t["rows"][0][0] == "Code")
        return fault["page"], fault["bbox"], _table_to_markdown(fault["rows"])

    def test_table_quote_highlights_single_row(self):
        """A quoted cell should highlight just its own row, not the whole table."""
        from app.services.highlights import find_table_highlight_rects
        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")
        page, bbox, md = self._fault_table_markdown()

        _, _, rects = find_table_highlight_rects(DEMO_PDF, page, md, "Check load; verify motor sizing")
        assert len(rects) == 1
        x0, y0, x1, y1 = rects[0]
        table_height = bbox[3] - bbox[1]
        assert (y1 - y0) < table_height / 4  # one row, not the entire table

    def test_table_without_matching_quote_highlights_whole_table(self):
        from app.services.highlights import find_table_highlight_rects
        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")
        page, bbox, md = self._fault_table_markdown()

        _, _, rects = find_table_highlight_rects(DEMO_PDF, page, md, "no such text qq zz")
        assert len(rects) == 1
        assert rects[0] == pytest.approx(bbox)

    def test_header_row_quote_is_ignored_not_highlighted_alone(self):
        """A quote that is just the header row must not shrink the highlight to the header."""
        from app.services.highlights import find_table_highlight_rects
        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")
        page, bbox, md = self._fault_table_markdown()

        header_quote = "| Code | Name | Possible Causes | Immediate Action |"
        _, _, rects = find_table_highlight_rects(DEMO_PDF, page, md, header_quote)
        assert len(rects) == 1
        assert rects[0] == pytest.approx(bbox)

    def test_fault_code_key_highlights_its_row(self):
        from app.services.highlights import find_table_highlight_rects
        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")
        page, bbox, md = self._fault_table_markdown()

        _, _, rects = find_table_highlight_rects(DEMO_PDF, page, md, "E09")
        assert len(rects) == 1
        assert (rects[0][3] - rects[0][1]) < (bbox[3] - bbox[1]) / 4

    def test_table_with_unknown_header_returns_empty(self):
        from app.services.highlights import find_table_highlight_rects
        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")
        page, _, _ = self._fault_table_markdown()

        _, _, rects = find_table_highlight_rects(DEMO_PDF, page, "| Nope | Nada |\n| --- | --- |", "x")
        assert rects == []

    def test_out_of_range_page_returns_empty(self):
        from app.services.highlights import find_highlight_rects

        if not os.path.exists(DEMO_PDF):
            pytest.skip("Demo PDF not found")

        page_width, page_height, rects = find_highlight_rects(DEMO_PDF, 9999, "anything")
        assert rects == []
