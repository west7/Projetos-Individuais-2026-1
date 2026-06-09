from sqlite3 import Row
import hashlib

from src.catalog import Catalog
from src.models import DocumentCandidate, DownloadedDocument, ExtractedMetric, ExtractionResult
from src.process import process_documents


def test_process_documents_mock_registers_metrics(tmp_path):
    db_path = tmp_path / "catalog.db"
    catalog = Catalog(db_path)
    candidate = DocumentCandidate(
        company="Pacaembu",
        source_name="Pacaembu RI",
        source_page_url="https://ri.pacaembu.com/",
        document_url="https://ri.pacaembu.com/a.pdf",
        document_title="Previa Operacional 3T25",
        year=2025,
        quarter=3,
    )
    sha256 = hashlib.sha256(b"%PDF test").hexdigest()
    document = DownloadedDocument(candidate, b"%PDF test", sha256, "data/pdfs/a.pdf")

    try:
        catalog.register_download(document)
    finally:
        catalog.close()

    stats = process_documents(db_path)

    catalog = Catalog(db_path)
    try:
        metrics = catalog.list_metrics()
        documents = catalog.list_documents()
    finally:
        catalog.close()

    assert stats == {"documents": 1, "metrics": 2, "parsed": 0, "failed": 0}
    assert {metric["metric_name"] for metric in metrics} == {"lancamentos", "vendas"}
    assert documents[0]["status"] == "extracted_mock"


def test_process_documents_gemini_can_use_fake_extractor(tmp_path, monkeypatch):
    db_path = tmp_path / "catalog.db"
    pdf_path = tmp_path / "a.pdf"
    pdf_path.write_bytes(b"%PDF fake")
    catalog = Catalog(db_path)
    candidate = DocumentCandidate(
        company="MRV",
        source_name="MRV RI",
        source_page_url="https://ri.mrv.com.br/",
        document_url="https://ri.mrv.com.br/a.pdf",
        document_title="Previa Operacional 1T26",
        year=2026,
        quarter=1,
    )
    sha256 = hashlib.sha256(b"%PDF fake").hexdigest()
    document = DownloadedDocument(candidate, b"%PDF fake", sha256, str(pdf_path))

    try:
        catalog.register_download(document)
        row = catalog.list_documents()[0]
        catalog.register_document_text(type("Parsed", (), {"document_id": row["id"], "page_count": 1, "text": "vendas 100"})())
    finally:
        catalog.close()

    class FakeGeminiExtractor:
        def extract(self, document: Row, document_text: str | None = None) -> ExtractionResult:
            assert document_text == "vendas 100"
            return ExtractionResult(
                company=document["company"],
                year=document["year"],
                quarter=document["quarter"],
                extractor_name="gemini-2.5-flash",
                metrics=[
                    ExtractedMetric(
                        metric_name="vendas",
                        value=100.0,
                        unit="R$ mil",
                        confidence="high",
                        evidence="vendas 100",
                    )
                ],
            )

    monkeypatch.setattr("src.process.GeminiLLMExtractor", FakeGeminiExtractor)

    stats = process_documents(db_path, extractor_name="gemini")

    assert stats == {"documents": 1, "metrics": 1, "parsed": 0, "failed": 0}
