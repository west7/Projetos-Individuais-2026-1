from pathlib import Path

from .catalog import Catalog
from .pdf_parser import parse_pdf_text


def parse_documents(db_path: Path, company: str | None = None, limit: int | None = None) -> dict[str, int]:
    catalog = Catalog(db_path)
    stats = {"documents": 0, "failed": 0}

    try:
        documents = catalog.documents_ready_for_parsing(company)
        for document in documents:
            if limit is not None and stats["documents"] >= limit:
                break
            try:
                parsed_text = parse_pdf_text(document["id"], document["local_path"])
                catalog.register_document_text(parsed_text)
                stats["documents"] += 1
            except Exception:
                stats["failed"] += 1
    finally:
        catalog.close()

    return stats
