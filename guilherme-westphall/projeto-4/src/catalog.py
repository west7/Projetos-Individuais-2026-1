import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import DocumentCandidate, DownloadedDocument


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

class Catalog:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(SCHEMA)
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
            SELECT company, year, quarter, status, document_title, document_url, local_path, sha256
            FROM documents
            ORDER BY company, year DESC, quarter DESC, document_title
            """
        ).fetchall()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
