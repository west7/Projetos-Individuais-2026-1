from src.downloader import build_filename, looks_like_pdf
from src.models import DocumentCandidate


def test_looks_like_pdf_accepts_pdf_signature():
    assert looks_like_pdf(b"%PDF-1.4\ncontent")


def test_looks_like_pdf_rejects_html():
    assert not looks_like_pdf(b"<html></html>")


def test_build_filename_contains_company_period_and_hash():
    candidate = DocumentCandidate(
        company="Pacaembu",
        source_name="Pacaembu RI",
        source_page_url="https://ri.pacaembu.com/",
        document_url="https://ri.pacaembu.com/previa.pdf",
        document_title="Previa Operacional 3T25",
        year=2025,
        quarter=3,
    )

    filename = build_filename(candidate, "abcdef1234567890")

    assert filename.startswith("pacaembu_2025_3t_")
    assert filename.endswith("_abcdef1234.pdf")
