"""
ForgeGuide AI — Core test suite.

Tests:
- PDF ingestion pipeline (text extraction, chunking, metadata)
- Bad upload rejection
- No-evidence behavior (regression: must NOT fabricate)
- Retrieval quality
- API input validation
- Equipment filtering
"""
import io
import os
import sys
import json
import tempfile
import pytest

# Make sure we can import from the app directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Unit tests: text extraction and chunking ────────────────────────────────

class TestChunkingLogic:
    def test_chunk_splits_long_text(self):
        from app.services.ingestion import _chunk_page_text
        long_text = "A" * 2400  # 3 chunks at 800 chars with 150 overlap
        chunks = _chunk_page_text(1, long_text)
        assert len(chunks) >= 2

    def test_chunk_discards_short_pages(self):
        from app.services.ingestion import _chunk_page_text
        short_text = "Too short"
        chunks = _chunk_page_text(1, short_text)
        assert chunks == []

    def test_chunk_preserves_page_number(self):
        from app.services.ingestion import _chunk_page_text
        text = "The MX-400 heat sink thermal overtemperature fault E17. " * 20
        chunks = _chunk_page_text(7, text)
        for c in chunks:
            assert c["page"] == 7

    def test_chunk_overlap(self):
        from app.services.ingestion import _chunk_page_text
        # Two chunks should share some text (overlap)
        text = "word " * 300  # ~1500 chars
        chunks = _chunk_page_text(1, text)
        assert len(chunks) >= 2
        # End of chunk 0 and start of chunk 1 should share content
        end_first = chunks[0]["text"][-50:].strip()
        start_second = chunks[1]["text"][:50].strip()
        # They should have some common tokens
        first_words = set(end_first.split())
        second_words = set(start_second.split())
        assert len(first_words & second_words) > 0


class TestSectionDetection:
    def test_detects_numbered_section(self):
        from app.services.ingestion import _detect_section
        text = "6.3 E17 — Thermal Overtemperature Fault\nThis fault indicates..."
        section = _detect_section(text, 1)
        assert section is not None
        assert "6.3" in section or "E17" in section

    def test_no_section_on_body_text(self):
        from app.services.ingestion import _detect_section
        text = "This is a paragraph of body text with no heading. It continues..."
        section = _detect_section(text, 1)
        # May or may not detect — just ensure no crash
        assert section is None or isinstance(section, str)


# ─── Unit tests: PDF extraction ─────────────────────────────────────────────

class TestPDFExtraction:
    def test_extract_real_demo_pdf(self):
        """Verify demo manual extracts text and preserves page numbers."""
        from app.services.ingestion import _extract_text_from_pdf
        demo_pdf = os.path.join(
            os.path.dirname(__file__), "..", "..", "demo-data",
            "MX400-Maintenance-Manual-DEMO.pdf"
        )
        if not os.path.exists(demo_pdf):
            pytest.skip("Demo PDF not found — run scripts/generate_demo_manual.py first")

        pages = _extract_text_from_pdf(demo_pdf)
        assert len(pages) > 0
        # Each page has a page number and text
        for p in pages:
            assert "page" in p
            assert isinstance(p["page"], int)
            assert p["page"] >= 1

    def test_demo_pdf_contains_e17(self):
        """Demo manual must contain E17 fault code content."""
        from app.services.ingestion import _extract_text_from_pdf
        demo_pdf = os.path.join(
            os.path.dirname(__file__), "..", "..", "demo-data",
            "MX400-Maintenance-Manual-DEMO.pdf"
        )
        if not os.path.exists(demo_pdf):
            pytest.skip("Demo PDF not found")

        pages = _extract_text_from_pdf(demo_pdf)
        full_text = " ".join(p["text"] for p in pages)
        assert "E17" in full_text
        assert "thermal" in full_text.lower() or "Thermal" in full_text

    def test_chunk_count_from_demo_pdf(self):
        """Demo manual should produce a reasonable number of chunks."""
        from app.services.ingestion import _extract_text_from_pdf, _chunk_page_text
        demo_pdf = os.path.join(
            os.path.dirname(__file__), "..", "..", "demo-data",
            "MX400-Maintenance-Manual-DEMO.pdf"
        )
        if not os.path.exists(demo_pdf):
            pytest.skip("Demo PDF not found")

        pages = _extract_text_from_pdf(demo_pdf)
        all_chunks = []
        for p in pages:
            all_chunks.extend(_chunk_page_text(p["page"], p["text"]))

        assert len(all_chunks) >= 5, f"Expected ≥5 chunks, got {len(all_chunks)}"


# ─── Unit tests: Upload validation ──────────────────────────────────────────

class TestUploadValidation:
    def test_safe_filename_strips_path(self):
        from app.api.documents import _safe_filename
        result = _safe_filename("../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_safe_filename_allows_normal(self):
        from app.api.documents import _safe_filename
        result = _safe_filename("MX400-Manual.pdf")
        assert "MX400" in result
        assert result.endswith(".pdf")

    def test_safe_filename_removes_special_chars(self):
        from app.api.documents import _safe_filename
        result = _safe_filename("file; rm -rf /.pdf")
        assert ";" not in result
        assert " " not in result


# ─── CRITICAL REGRESSION: No evidence = no fabrication ──────────────────────

class TestNoEvidenceBehavior:
    """
    REGRESSION TEST: ForgeGuide must NOT fabricate a maintenance procedure
    when no supporting document evidence exists.
    """

    def _make_no_op_retriever(self):
        """Patch retrieve to return empty results."""
        return []

    def test_insufficient_evidence_response_when_no_chunks(self, monkeypatch):
        """When retrieval returns nothing, QA must refuse to answer."""
        from app.services import qa

        # Patch retrieve to return empty
        monkeypatch.setattr("app.services.qa.retrieve", lambda db, q, **kw: [])

        result = qa.answer(db=None, question="How do I replace the IGBT module?")

        assert result.evidence_sufficient is False
        assert "INSUFFICIENT_EVIDENCE" in result.answer or result.confidence == 0.0
        assert result.citations == []

    def test_insufficient_evidence_response_low_confidence(self, monkeypatch):
        """Low-confidence retrieval also triggers the no-evidence gate."""
        from app.services import qa

        # Return chunks with zero fused score
        fake_chunks = [{
            "chunk_id": "fake-1",
            "document_id": "doc-1",
            "document_title": "Unrelated Doc",
            "equipment_id": None,
            "page": 1,
            "section": None,
            "text": "This is completely unrelated content about something else.",
            "fused_score": 0.01,
            "score": 0.01,
        }]
        monkeypatch.setattr("app.services.qa.retrieve", lambda db, q, **kw: fake_chunks)

        result = qa.answer(db=None, question="What is the thermal shutdown sequence?")

        # Confidence should be very low → decline
        assert result.confidence < qa.settings.evidence_confidence_threshold
        assert result.evidence_sufficient is False

    def test_answer_contains_no_fabrication_marker(self, monkeypatch):
        """The word 'INSUFFICIENT_EVIDENCE' must appear in answer when declining."""
        from app.services import qa

        monkeypatch.setattr("app.services.qa.retrieve", lambda db, q, **kw: [])

        result = qa.answer(db=None, question="Walk me through the E17 fix procedure.")

        # Must clearly decline, not invent steps
        assert "INSUFFICIENT_EVIDENCE" in result.answer
        # Must NOT include numbered step-by-step procedure
        assert "1." not in result.answer[:200]


# ─── Unit tests: Citation parsing ────────────────────────────────────────────

class TestCitationParsing:
    def test_parses_valid_citations_block(self):
        from app.services.qa import _parse_citations
        raw = """The heat sink should be inspected.

```citations
[{"document": "MX-400 Manual", "page": 8, "section": "4.1", "excerpt": "Inspect fan blades"}]
```"""
        chunks = [{"document_title": "MX-400 Manual", "page": 8, "chunk_id": "c1", "document_id": "d1"}]
        clean, citations = _parse_citations(raw, chunks)
        assert len(citations) == 1
        assert citations[0].page == 8
        assert citations[0].document == "MX-400 Manual"
        assert "```citations" not in clean

    def test_parses_json_fenced_citations_block(self):
        # Smaller/local models often use ```json instead of the requested
        # ```citations fence — regression test for that fallback path.
        from app.services.qa import _parse_citations
        raw = """The heat sink should be inspected.

Citations:
```json
[{"document": "MX-400 Manual", "page": 8, "section": "4.1", "excerpt": "Inspect fan blades"}]
```"""
        chunks = [{"document_title": "MX-400 Manual", "page": 8, "chunk_id": "c1", "document_id": "d1"}]
        clean, citations = _parse_citations(raw, chunks)
        assert len(citations) == 1
        assert citations[0].page == 8
        assert citations[0].document == "MX-400 Manual"
        assert "```" not in clean
        assert "Citations:" not in clean

    def test_handles_missing_citations_block(self):
        from app.services.qa import _parse_citations
        raw = "Answer without any citation block."
        clean, citations = _parse_citations(raw, [])
        assert citations == []
        assert clean == raw

    def test_handles_malformed_json(self):
        from app.services.qa import _parse_citations
        raw = "Answer\n```citations\n{not valid json}\n```"
        clean, citations = _parse_citations(raw, [])
        # Should not raise — just return empty citations
        assert isinstance(citations, list)


# ─── Unit tests: Fault code extraction ──────────────────────────────────────

class TestFaultCodeExtraction:
    def test_extracts_standard_fault_codes(self):
        import re
        from app.services.vision import FAULT_CODE_PATTERN
        text = "Display shows E17 and then E09. Unit shut down."
        codes = FAULT_CODE_PATTERN.findall(text)
        assert "E17" in codes
        assert "E09" in codes

    def test_no_false_positives_on_normal_words(self):
        from app.services.vision import FAULT_CODE_PATTERN
        text = "Check the motor and drive system for faults."
        codes = FAULT_CODE_PATTERN.findall(text)
        # Common words should not match
        assert "Check" not in codes

    def test_suggested_query_built_from_codes(self):
        """Suggested query must include detected fault codes."""
        from app.services.vision import extract_fault_codes

        # Patch to avoid real image/LLM call
        import unittest.mock as mock
        with mock.patch("app.services.vision._extract_via_ocr", return_value="Display: E17\nStatus: FAULT"):
            result = extract_fault_codes("/fake/image.jpg", use_vision=False)

        assert "E17" in result["fault_codes"]
        assert "E17" in result["suggested_query"]


# ─── Unit tests: RRF fusion ──────────────────────────────────────────────────

class TestRRFFusion:
    def test_rrf_boosts_items_in_both_lists(self):
        from app.services.retrieval import _rrf_fuse
        semantic = [{"chunk_id": "a", "document_title": "D", "page": 1, "section": None,
                     "text": "t", "document_id": "d1", "equipment_id": None, "score": 0.9}]
        keyword = [{"chunk_id": "a", "document_title": "D", "page": 1, "section": None,
                    "text": "t", "document_id": "d1", "equipment_id": None, "score": None}]
        merged = _rrf_fuse(semantic, keyword)
        assert len(merged) == 1
        # Item in both lists should have higher fused score than if in only one
        assert merged[0]["fused_score"] > 1 / (60 + 1)

    def test_rrf_deduplicates(self):
        from app.services.retrieval import _rrf_fuse
        chunk = {"chunk_id": "dup", "document_title": "D", "page": 1, "section": None,
                 "text": "t", "document_id": "d1", "equipment_id": None, "score": 0.5}
        merged = _rrf_fuse([chunk], [chunk])
        # Should not have duplicates
        ids = [m["chunk_id"] for m in merged]
        assert len(ids) == len(set(ids))
