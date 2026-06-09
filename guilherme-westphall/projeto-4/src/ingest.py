from pathlib import Path

from .catalog import Catalog
from .downloader import download_pdf
from .models import DocumentCandidate
from .scraper import discover_candidates, fetch_html
from .sources import Source


def ingest_sources(
    sources: list[Source],
    db_path: Path,
    output_dir: Path,
    limit: int | None = None,
) -> dict[str, int]:
    catalog = Catalog(db_path)
    stats = {"discovered": 0, "downloaded": 0, "skipped": 0, "failed": 0}

    try:
        for source in sources:
            try:
                html = fetch_html(source.url)
            except Exception:
                stats["failed"] += 1
                candidates = []
            else:
                candidates = discover_candidates(source, html)

            candidates.extend(_seed_candidates(source))
            candidates = _deduplicate_candidates(candidates)
            stats["discovered"] += len(candidates)

            for candidate in candidates:
                if limit is not None and stats["downloaded"] >= limit:
                    return stats

                if catalog.has_url(candidate.document_url):
                    stats["skipped"] += 1
                    continue

                try:
                    document = download_pdf(candidate, output_dir)
                except Exception:
                    catalog.register_candidate_for_review(candidate)
                    stats["failed"] += 1
                    continue

                if catalog.register_download(document):
                    stats["downloaded"] += 1
                else:
                    stats["skipped"] += 1
    finally:
        catalog.close()

    return stats


def _seed_candidates(source: Source) -> list[DocumentCandidate]:
    return [
        DocumentCandidate(
            company=source.company,
            source_name=source.name,
            source_page_url=source.url,
            document_url=document.url,
            document_title=document.title,
            year=document.year,
            quarter=document.quarter,
        )
        for document in source.seed_documents
    ]


def _deduplicate_candidates(candidates: list[DocumentCandidate]) -> list[DocumentCandidate]:
    seen: set[str] = set()
    unique: list[DocumentCandidate] = []
    for candidate in candidates:
        if candidate.document_url in seen:
            continue
        seen.add(candidate.document_url)
        unique.append(candidate)
    return unique
