import hashlib

from src.catalog import Catalog
from src.models import DocumentCandidate, DownloadedDocument
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

    assert stats == {"documents": 1, "metrics": 2}
    assert {metric["metric_name"] for metric in metrics} == {"lancamentos", "vendas"}
    assert documents[0]["status"] == "extracted_mock"
