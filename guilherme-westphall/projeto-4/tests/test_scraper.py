from src.scraper import discover_candidates, infer_period
from src.sources import Source


def test_infer_period_short_year():
    assert infer_period("Previa Operacional 1T26") == (2026, 1)


def test_infer_period_full_year():
    assert infer_period("Release de Resultados 3T2025") == (2025, 3)


def test_discover_candidates_finds_relevant_pdf_links():
    source = Source(company="MRV", name="MRV RI", url="https://ri.example.com/resultados/")
    html = """
    <section>
      <h3>1T26</h3>
      <a href="/docs/previa-operacional-1t26.pdf">Previa Operacional</a>
      <a href="/docs/audio-1t26.mp3">Audio</a>
      <a href="/docs/itr-1t26.pdf">ITR</a>
    </section>
    """

    candidates = discover_candidates(source, html)

    assert len(candidates) == 1
    assert candidates[0].document_url == "https://ri.example.com/docs/previa-operacional-1t26.pdf"
    assert candidates[0].year == 2026
    assert candidates[0].quarter == 1
