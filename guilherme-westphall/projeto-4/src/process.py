from pathlib import Path

from .catalog import Catalog
from .extractor import GeminiLLMExtractor, MockLLMExtractor
from .pdf_parser import parse_pdf_text


def process_documents(
    db_path: Path,
    company: str | None = None,
    limit: int | None = None,
    extractor_name: str = "mock",
) -> dict[str, int]:
    catalog = Catalog(db_path)
    extractor = _build_extractor(extractor_name)
    stats = {"documents": 0, "metrics": 0, "parsed": 0, "failed": 0}

    try:
        documents = catalog.documents_ready_for_extraction(company)
        for document in documents:
            if limit is not None and stats["documents"] >= limit:
                break
            try:
                had_cached_text = catalog.get_document_text(document["id"]) is not None
                document_text = _load_or_parse_text(catalog, document) if extractor_name == "gemini" else None
                if document_text is not None and not had_cached_text:
                    stats["parsed"] += 1
                result = extractor.extract(document, document_text)
                stats["metrics"] += catalog.register_extraction(document["id"], result)
                stats["documents"] += 1
            except Exception as exc:
                if extractor_name == "gemini" and "GEMINI_API_KEY" in str(exc):
                    raise
                stats["failed"] += 1
    finally:
        catalog.close()

    return stats


def _build_extractor(extractor_name: str):
    if extractor_name == "mock":
        return MockLLMExtractor()
    if extractor_name == "gemini":
        return GeminiLLMExtractor()
    raise ValueError("Extrator invalido. Use 'mock' ou 'gemini'.")


def _load_or_parse_text(catalog: Catalog, document) -> str:
    cached = catalog.get_document_text(document["id"])
    if cached is not None:
        return cached["text"]

    parsed_text = parse_pdf_text(document["id"], document["local_path"])
    catalog.register_document_text(parsed_text)
    return parsed_text.text
