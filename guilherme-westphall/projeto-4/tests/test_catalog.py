import hashlib

from src.catalog import Catalog
from src.models import DocumentCandidate, DownloadedDocument


def test_catalog_register_download_is_idempotent_by_hash(tmp_path):
    catalog = Catalog(tmp_path / "catalog.db")
    candidate = DocumentCandidate(
        company="MRV",
        source_name="MRV RI",
        source_page_url="https://ri.mrv.com.br/",
        document_url="https://ri.mrv.com.br/a.pdf",
        document_title="Previa Operacional 1T26",
        year=2026,
        quarter=1,
    )
    sha256 = hashlib.sha256(b"%PDF test").hexdigest()
    document = DownloadedDocument(candidate, b"%PDF test", sha256, "data/pdfs/a.pdf")

    try:
        assert catalog.register_download(document)
        assert not catalog.register_download(document)
        assert len(catalog.list_documents()) == 1
    finally:
        catalog.close()
