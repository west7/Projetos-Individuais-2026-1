import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import DocumentCandidate
from .sources import Source

DOCUMENT_KEYWORDS = (
    "previa operacional",
    "prévia operacional",
    "release de resultados",
    "earnings release",
)


def fetch_html(url: str, timeout: int = 20) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "projeto-4-uda-ingestion/1.0"},
    )
    response.raise_for_status()
    return response.text


def discover_candidates(source: Source, html: str) -> list[DocumentCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[DocumentCandidate] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        absolute_url = urljoin(source.url, href)
        link_text = link.get_text(" ", strip=True)
        context = _context_text(link)
        normalized_link = _normalize(link_text + " " + absolute_url)
        normalized_context = _normalize(context + " " + absolute_url)

        normalized_link_text = _normalize(link_text)
        if not _is_document_candidate(absolute_url, normalized_link, normalized_link_text, normalized_context):
            continue
        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)
        year, quarter = infer_period(context + " " + absolute_url)
        candidates.append(
            DocumentCandidate(
                company=source.company,
                source_name=source.name,
                source_page_url=source.url,
                document_url=absolute_url,
                document_title=_clean_title(context) or absolute_url,
                year=year,
                quarter=quarter,
            )
        )

    return candidates


def infer_period(text: str) -> tuple[int | None, int | None]:
    normalized = _normalize(text)
    match = re.search(r"\b([1-4])\s*t\s*(20)?(\d{2})\b", normalized)
    if not match:
        return None, None

    quarter = int(match.group(1))
    year_suffix = int(match.group(3))
    year = 2000 + year_suffix
    return year, quarter


def _is_document_candidate(
    url: str,
    normalized_link: str,
    normalized_link_text: str,
    normalized_context: str,
) -> bool:
    has_pdf_signal = ".pdf" in url.lower() or "download.aspx" in url.lower() or "mzfilemanager" in url.lower()
    has_keyword = any(keyword in normalized_link for keyword in DOCUMENT_KEYWORDS)
    generic_link = any(word in normalized_link_text for word in ("download", "baixar", "pdf", "arquivo"))
    has_context_keyword = generic_link and any(keyword in normalized_context for keyword in DOCUMENT_KEYWORDS)
    has_keyword = has_keyword or has_context_keyword
    return has_pdf_signal and has_keyword


def _context_text(link) -> str:
    parts = [link.get_text(" ", strip=True)]
    parent = link.parent
    for _ in range(3):
        if parent is None:
            break
        parts.append(parent.get_text(" ", strip=True))
        parent = parent.parent
    return " ".join(parts)


def _clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()
