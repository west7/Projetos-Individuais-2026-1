from pathlib import Path

from .models import ParsedDocumentText


class PdfParsingError(ValueError):
    pass


def parse_pdf_text(document_id: int, local_path: str | Path) -> ParsedDocumentText:
    path = Path(local_path)
    if not path.exists():
        raise PdfParsingError(f"PDF nao encontrado: {path}")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PdfParsingError("pypdf nao esta instalado. Rode `pip install -r requirements.txt`.") from exc

    pages: list[str] = []
    reader = PdfReader(path)
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"--- pagina {page_number} ---\n{text}")
    page_count = len(reader.pages)

    full_text = "\n\n".join(pages).strip()
    if not full_text:
        raise PdfParsingError(f"Nenhum texto extraido do PDF: {path}")

    return ParsedDocumentText(document_id=document_id, page_count=page_count, text=full_text)
