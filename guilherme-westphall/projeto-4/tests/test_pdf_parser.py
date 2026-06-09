from pathlib import Path

import pytest

from src.pdf_parser import PdfParsingError, parse_pdf_text


def test_parse_pdf_text_extracts_text():
    pytest.importorskip("pypdf")
    pdf_path = (
        Path(__file__).resolve().parents[3]
        / "projeto-individual-4"
        / "exemplo_Boletim_Conjuntura_2025_3T.pdf"
    )

    parsed = parse_pdf_text(10, pdf_path)

    assert parsed.document_id == 10
    assert parsed.page_count == 1
    assert "Conjuntura do Setor Habitacional" in parsed.text


def test_parse_pdf_text_rejects_missing_file(tmp_path):
    with pytest.raises(PdfParsingError):
        parse_pdf_text(1, tmp_path / "missing.pdf")
