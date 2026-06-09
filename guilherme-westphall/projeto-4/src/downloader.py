import hashlib
import re
from pathlib import Path

import requests

from .models import DocumentCandidate, DownloadedDocument


def download_pdf(candidate: DocumentCandidate, output_dir: Path, timeout: int = 30) -> DownloadedDocument:
    response = requests.get(
        candidate.document_url,
        timeout=timeout,
        headers={"User-Agent": "projeto-4-uda-ingestion/1.0"},
    )
    response.raise_for_status()

    content = response.content
    if not looks_like_pdf(content):
        raise ValueError(f"Documento nao parece PDF: {candidate.document_url}")

    sha256 = hashlib.sha256(content).hexdigest()
    filename = build_filename(candidate, sha256)
    output_dir.mkdir(parents=True, exist_ok=True)
    local_path = output_dir / filename
    local_path.write_bytes(content)

    return DownloadedDocument(
        candidate=candidate,
        content=content,
        sha256=sha256,
        local_path=str(local_path),
    )


def looks_like_pdf(content: bytes) -> bool:
    return content.lstrip().startswith(b"%PDF")


def build_filename(candidate: DocumentCandidate, sha256: str) -> str:
    year = candidate.year or "ano-desconhecido"
    quarter = f"{candidate.quarter}t" if candidate.quarter else "tri-desconhecido"
    title = slugify(candidate.document_title)[:60] or "documento"
    return f"{slugify(candidate.company)}_{year}_{quarter}_{title}_{sha256[:10]}.pdf"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")
