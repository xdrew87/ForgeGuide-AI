"""
Multimodal: extract fault codes from equipment images.
Supports: anthropic (Claude vision), openai (GPT-4o), ollama (llava/moondream),
          tesseract (offline fallback — no LLM needed).
"""
import logging
import re
import base64
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FAULT_CODE_PATTERN = re.compile(r"\b[A-Z]{1,3}[-]?\d{1,4}\b")

VISION_PROMPT = (
    "Extract all visible text from this industrial equipment image. "
    "Focus on: fault codes, error codes, display readings, labels, and status indicators. "
    "List each item on its own line. Do not interpret — only transcribe what you see."
)


def _load_image_b64(image_path: str) -> tuple[str, str]:
    """Returns (base64_data, media_type)."""
    suffix = Path(image_path).suffix.lower()
    media_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_map.get(suffix, "image/jpeg")
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("utf-8")
    return b64, media_type


def _extract_via_anthropic(image_path: str) -> str:
    import anthropic
    b64, media_type = _load_image_b64(image_path)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64},
                },
                {"type": "text", "text": VISION_PROMPT},
            ],
        }]
    )
    return response.content[0].text


def _extract_via_openai(image_path: str) -> str:
    import openai
    b64, media_type = _load_image_b64(image_path)
    client = openai.OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{b64}"},
                },
                {"type": "text", "text": VISION_PROMPT},
            ],
        }]
    )
    return response.choices[0].message.content


def _extract_via_ollama(image_path: str) -> str:
    """
    Ollama multimodal via /api/chat with images field.
    Works with vision-capable models: llava, llava-phi3, moondream, bakllava.
    Falls back to OCR if the configured model isn't vision-capable.
    """
    import httpx
    b64, _ = _load_image_b64(image_path)
    base_url = settings.ollama_base_url.rstrip("/")

    # Use the dedicated vision model if configured, otherwise try main model
    vision_model = settings.ollama_vision_model or settings.llm_model

    try:
        response = httpx.post(
            f"{base_url}/api/chat",
            json={
                "model": vision_model,
                "messages": [{
                    "role": "user",
                    "content": VISION_PROMPT,
                    "images": [b64],
                }],
                "stream": False,
                "options": {"num_predict": 500, "temperature": 0.0},
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except Exception as e:
        logger.warning(f"Ollama vision failed ({vision_model}): {e} — falling back to OCR")
        return _extract_via_ocr(image_path)


def _extract_via_ocr(image_path: str) -> str:
    """Tesseract OCR — offline, no API key required."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, config="--psm 6")
    except Exception as e:
        logger.error(f"OCR fallback failed: {e}")
        return ""


def extract_fault_codes(image_path: str, use_vision: bool = True) -> dict:
    """
    Extract fault codes from an equipment image.
    Provider is selected from settings (llm_provider).
    Returns: {raw_text, fault_codes, suggested_query}
    """
    raw_text = ""

    if use_vision:
        provider = settings.llm_provider
        try:
            if provider == "anthropic" and settings.anthropic_api_key:
                raw_text = _extract_via_anthropic(image_path)
            elif provider == "openai" and settings.openai_api_key:
                raw_text = _extract_via_openai(image_path)
            elif provider == "ollama":
                raw_text = _extract_via_ollama(image_path)
            else:
                raw_text = _extract_via_ocr(image_path)
        except Exception as e:
            logger.warning(f"Vision extraction failed: {e} — falling back to OCR")
            raw_text = _extract_via_ocr(image_path)
    else:
        raw_text = _extract_via_ocr(image_path)

    fault_codes = list(dict.fromkeys(FAULT_CODE_PATTERN.findall(raw_text)))

    suggested_query = (
        f"Fault code {' '.join(fault_codes)} troubleshooting procedure"
        if fault_codes
        else raw_text[:200]
    )

    return {
        "raw_text": raw_text,
        "fault_codes": fault_codes,
        "suggested_query": suggested_query,
    }
