import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import DocumentCandidate, DownloadedDocument, ExtractionResult, ParsedDocumentText


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_page_url TEXT NOT NULL,
    document_url TEXT NOT NULL UNIQUE,
    document_title TEXT NOT NULL,
    year INTEGER,
    quarter INTEGER,
    sha256 TEXT UNIQUE,
    local_path TEXT,
    status TEXT NOT NULL,
    discovered_at TEXT NOT NULL,
    downloaded_at TEXT
);
"""

METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    company TEXT NOT NULL,
    year INTEGER,
    quarter INTEGER,
    metric_name TEXT NOT NULL,
    value REAL,
    unit TEXT NOT NULL,
    confidence TEXT NOT NULL,
    evidence TEXT,
    extractor_name TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);
"""

DOCUMENT_TEXTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS document_texts (
    document_id INTEGER PRIMARY KEY,
    page_count INTEGER NOT NULL,
    text TEXT NOT NULL,
    parsed_at TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);
"""


class Catalog:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(SCHEMA)
        self.connection.execute(METRICS_SCHEMA)
        self.connection.execute(DOCUMENT_TEXTS_SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def has_url(self, document_url: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM documents WHERE document_url = ? LIMIT 1",
            (document_url,),
        ).fetchone()
        return row is not None

    def has_sha256(self, sha256: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM documents WHERE sha256 = ? LIMIT 1",
            (sha256,),
        ).fetchone()
        return row is not None

    def register_candidate_for_review(self, candidate: DocumentCandidate) -> None:
        if self.has_url(candidate.document_url):
            return
        now = _now()
        self.connection.execute(
            """
            INSERT INTO documents (
                company, source_name, source_page_url, document_url, document_title,
                year, quarter, sha256, local_path, status, discovered_at, downloaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL)
            """,
            (
                candidate.company,
                candidate.source_name,
                candidate.source_page_url,
                candidate.document_url,
                candidate.document_title,
                candidate.year,
                candidate.quarter,
                "needs_manual_review",
                now,
            ),
        )
        self.connection.commit()

    def register_download(self, document: DownloadedDocument) -> bool:
        if self.has_sha256(document.sha256):
            return False

        candidate = document.candidate
        now = _now()
        self.connection.execute(
            """
            INSERT INTO documents (
                company, source_name, source_page_url, document_url, document_title,
                year, quarter, sha256, local_path, status, discovered_at, downloaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_url) DO UPDATE SET
                sha256 = excluded.sha256,
                local_path = excluded.local_path,
                status = excluded.status,
                downloaded_at = excluded.downloaded_at
            """,
            (
                candidate.company,
                candidate.source_name,
                candidate.source_page_url,
                candidate.document_url,
                candidate.document_title,
                candidate.year,
                candidate.quarter,
                document.sha256,
                document.local_path,
                "downloaded",
                now,
                now,
            ),
        )
        self.connection.commit()
        return True

    def list_documents(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT id, company, year, quarter, status, document_title, document_url, local_path, sha256
            FROM documents
            ORDER BY company, year DESC, quarter DESC, document_title
            """
        ).fetchall()

    def documents_ready_for_extraction(self, company: str | None = None) -> list[sqlite3.Row]:
        params: tuple[str, ...] = ()
        company_filter = ""
        if company:
            company_filter = "AND lower(company) = lower(?)"
            params = (company,)

        return self.connection.execute(
            f"""
            SELECT id, company, year, quarter, document_title, document_url, local_path
            FROM documents
            WHERE status IN ('downloaded', 'parsed', 'extracted_mock', 'extracted_gemini')
              AND local_path IS NOT NULL
              {company_filter}
            ORDER BY company, year DESC, quarter DESC, document_title
            """,
            params,
        ).fetchall()

    def register_document_text(self, parsed_text: ParsedDocumentText) -> None:
        now = _now()
        self.connection.execute(
            """
            INSERT INTO document_texts (document_id, page_count, text, parsed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                page_count = excluded.page_count,
                text = excluded.text,
                parsed_at = excluded.parsed_at
            """,
            (parsed_text.document_id, parsed_text.page_count, parsed_text.text, now),
        )
        self.connection.execute(
            "UPDATE documents SET status = ? WHERE id = ? AND status = ?",
            ("parsed", parsed_text.document_id, "downloaded"),
        )
        self.connection.commit()

    def get_document_text(self, document_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            """
            SELECT document_id, page_count, text, parsed_at
            FROM document_texts
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

    def documents_ready_for_parsing(self, company: str | None = None) -> list[sqlite3.Row]:
        params: tuple[str, ...] = ()
        company_filter = ""
        if company:
            company_filter = "AND lower(company) = lower(?)"
            params = (company,)

        return self.connection.execute(
            f"""
            SELECT id, company, year, quarter, document_title, document_url, local_path
            FROM documents
            WHERE status IN ('downloaded', 'parsed', 'extracted_mock', 'extracted_gemini')
              AND local_path IS NOT NULL
              {company_filter}
            ORDER BY company, year DESC, quarter DESC, document_title
            """,
            params,
        ).fetchall()

    def register_extraction(self, document_id: int, result: ExtractionResult, status: str | None = None) -> int:
        now = _now()
        self.connection.execute("DELETE FROM metrics WHERE document_id = ?", (document_id,))

        for metric in result.metrics:
            self.connection.execute(
                """
                INSERT INTO metrics (
                    document_id, company, year, quarter, metric_name, value, unit,
                    confidence, evidence, extractor_name, extracted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    result.company,
                    result.year,
                    result.quarter,
                    metric.metric_name,
                    metric.value,
                    metric.unit,
                    metric.confidence,
                    metric.evidence,
                    result.extractor_name,
                    now,
                ),
            )

        extraction_status = status or _status_for_extractor(result.extractor_name)
        self.connection.execute(
            "UPDATE documents SET status = ? WHERE id = ?",
            (extraction_status, document_id),
        )
        self.connection.commit()
        return len(result.metrics)

    def list_metrics(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT company, year, quarter, metric_name, value, unit, confidence, extractor_name
            FROM metrics
            ORDER BY company, year DESC, quarter DESC, metric_name
            """
        ).fetchall()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_for_extractor(extractor_name: str) -> str:
    if "gemini" in extractor_name:
        return "extracted_gemini"
    return "extracted_mock"
