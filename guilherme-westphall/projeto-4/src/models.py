from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentCandidate:
    company: str
    source_name: str
    source_page_url: str
    document_url: str
    document_title: str
    year: int | None
    quarter: int | None


@dataclass(frozen=True)
class DownloadedDocument:
    candidate: DocumentCandidate
    content: bytes
    sha256: str
    local_path: str
