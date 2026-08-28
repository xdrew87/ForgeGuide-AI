"""
Grounded QA: assemble context from retrieved chunks, call LLM, return
citations. If evidence is insufficient, decline — do not fabricate.

Supports: anthropic, openai, ollama
"""
import json
import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.retrieval import retrieve

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are ForgeGuide AI, an industrial maintenance assistant.

RULES — follow these exactly:
1. Answer ONLY based on the provided documentation excerpts (CONTEXT).
2. If the context does not contain sufficient evidence to answer safely and accurately, respond with the INSUFFICIENT_EVIDENCE marker and explain what is missing.
3. Never invent, extrapolate, or assume maintenance procedures, fault causes, or safety steps beyond what is explicitly in the context.
4. Never recommend disabling safety controls, lockout/tagout, interlocks, or protective systems.
5. Always cite the source: document title, page number, and section for every factual claim.
6. Flag any safety-critical content clearly with [SAFETY-CRITICAL].
7. Distinguish between retrieved documentation (EVIDENCE) and your synthesis (SYNTHESIS).

RESPONSE FORMAT:
- Use plain text with clear structure.
- At the end, output a JSON block tagged ```citations containing an array of citation objects.
- Each citation object: {"document": "...", "page": N, "section": "...", "excerpt": "first 120 chars of supporting text"}

INSUFFICIENT_EVIDENCE marker: If evidence is insufficient, begin your response with:
<<INSUFFICIENT_EVIDENCE>>
Then explain what documentation is missing or why you cannot answer safely.
"""

CONTEXT_TEMPLATE = """
--- DOCUMENTATION CONTEXT ---
{context_blocks}
--- END CONTEXT ---

TECHNICIAN QUESTION:
{question}
"""


@dataclass
class Citation:
    document: str
    page: int
    section: str | None
    excerpt: str
    chunk_id: str
    document_id: str


@dataclass
class QAResult:
    question: str
    answer: str
    citations: list[Citation]
    evidence_sufficient: bool
    confidence: float
    chunks_used: int


def _build_context(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks):
        section_str = f", Section: {c['section']}" if c.get("section") else ""
        blocks.append(
            f"[SOURCE {i+1}] Document: {c['document_title']} | Page: {c['page']}{section_str}\n"
            f"{c['text']}\n"
        )
    return "\n".join(blocks)


def _call_llm(messages: list[dict]) -> str:
    provider = settings.llm_provider

    if provider == "anthropic":
        return _call_anthropic(messages)
    elif provider == "openai":
        return _call_openai(messages)
    elif provider == "ollama":
        return _call_ollama(messages)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _call_anthropic(messages: list[dict]) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


def _call_openai(messages: list[dict]) -> str:
    import openai
    client = openai.OpenAI(api_key=settings.openai_api_key)
    all_msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=all_msgs,
        max_tokens=1500,
    )
    return response.choices[0].message.content


def _call_ollama(messages: list[dict]) -> str:
    """
    Ollama /api/chat endpoint — OpenAI-compatible chat format.
    System prompt injected as first message.
    """
    import httpx
    base_url = settings.ollama_base_url.rstrip("/")

    all_msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = httpx.post(
        f"{base_url}/api/chat",
        json={
            "model": settings.llm_model,
            "messages": all_msgs,
            "stream": False,
            "options": {
                "num_predict": 1500,
                "temperature": 0.1,   # low temp for factual retrieval tasks
            },
        },
        timeout=300,  # local models can be slow
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def _parse_citations(raw_text: str, chunks: list[dict]) -> tuple[str, list[Citation]]:
    """Extract ```citations JSON block from raw LLM output."""
    import re
    citations = []
    clean_text = raw_text

    match = re.search(r"```citations\s*([\s\S]*?)```", raw_text)
    if match:
        clean_text = raw_text[:match.start()].strip()
        try:
            cite_data = json.loads(match.group(1).strip())
            for c in cite_data:
                matching = next(
                    (ch for ch in chunks
                     if ch["document_title"] == c.get("document")
                     and ch["page"] == c.get("page")),
                    None
                )
                citations.append(Citation(
                    document=c.get("document", "Unknown"),
                    page=c.get("page", 0),
                    section=c.get("section"),
                    excerpt=c.get("excerpt", "")[:150],
                    chunk_id=matching["chunk_id"] if matching else "",
                    document_id=matching["document_id"] if matching else "",
                ))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Citation parse failed: {e}")

    return clean_text, citations


def _estimate_confidence(chunks: list[dict]) -> float:
    if not chunks:
        return 0.0
    scores = [c.get("fused_score", 0) or c.get("score", 0) or 0 for c in chunks]
    avg_score = sum(scores) / len(scores)
    coverage_factor = min(len(chunks) / 3, 1.0)
    return round(min(avg_score * 10 * coverage_factor, 1.0), 2)


def answer(db: Session, question: str, equipment_id: str | None = None) -> QAResult:
    chunks = retrieve(db, question, equipment_id=equipment_id, top_k=6)
    confidence = _estimate_confidence(chunks)

    if not chunks or confidence < settings.evidence_confidence_threshold:
        return QAResult(
            question=question,
            answer=(
                "<<INSUFFICIENT_EVIDENCE>>\n\n"
                "I was unable to find supporting documentation in the uploaded manuals "
                "to answer this question safely. Please upload the relevant technical "
                "manual or maintenance procedure before asking this question.\n\n"
                "ForgeGuide AI does not generate unsupported maintenance recommendations."
            ),
            citations=[],
            evidence_sufficient=False,
            confidence=confidence,
            chunks_used=len(chunks),
        )

    context = _build_context(chunks)
    prompt = CONTEXT_TEMPLATE.format(context_blocks=context, question=question)
    messages = [{"role": "user", "content": prompt}]

    raw = _call_llm(messages)

    evidence_sufficient = "<<INSUFFICIENT_EVIDENCE>>" not in raw
    clean_answer, citations = _parse_citations(raw, chunks)

    return QAResult(
        question=question,
        answer=clean_answer,
        citations=citations,
        evidence_sufficient=evidence_sufficient,
        confidence=confidence if evidence_sufficient else 0.0,
        chunks_used=len(chunks),
    )
