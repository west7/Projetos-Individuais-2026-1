import pytest

from src.extractor import GeminiLLMExtractor


def test_gemini_extractor_requires_api_key(monkeypatch):
    pytest.importorskip("google.genai")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    extractor = GeminiLLMExtractor(load_env=False)
    document = {
        "company": "MRV",
        "year": 2026,
        "quarter": 1,
        "document_title": "Previa Operacional 1T26",
        "document_url": "https://example.com/a.pdf",
    }

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        extractor.extract(document, "texto do pdf")
