from pathlib import Path

from .catalog import Catalog
from .extractor import MockLLMExtractor


def process_documents(db_path: Path, company: str | None = None, limit: int | None = None) -> dict[str, int]:
    catalog = Catalog(db_path)
    extractor = MockLLMExtractor()
    stats = {"documents": 0, "metrics": 0}

    try:
        documents = catalog.documents_ready_for_extraction(company)
        for document in documents:
            if limit is not None and stats["documents"] >= limit:
                break
            result = extractor.extract(document)
            stats["metrics"] += catalog.register_extraction(document["id"], result)
            stats["documents"] += 1
    finally:
        catalog.close()

    return stats
