import hashlib
from sqlite3 import Row

from .models import ExtractedMetric, ExtractionResult


class MockLLMExtractor:
    name = "mock-llm-v1"

    def extract(self, document: Row) -> ExtractionResult:
        company = document["company"]
        year = document["year"]
        quarter = document["quarter"]
        seed = f"{company}|{year}|{quarter}|{document['document_url']}"

        return ExtractionResult(
            company=company,
            year=year,
            quarter=quarter,
            extractor_name=self.name,
            metrics=[
                ExtractedMetric(
                    metric_name="lancamentos",
                    value=_mock_value(seed, "lancamentos"),
                    unit="R$ mil",
                    confidence="mock",
                    evidence="Valor simulado para validar contrato e persistencia.",
                ),
                ExtractedMetric(
                    metric_name="vendas",
                    value=_mock_value(seed, "vendas"),
                    unit="R$ mil",
                    confidence="mock",
                    evidence="Valor simulado para validar contrato e persistencia.",
                ),
            ],
        )


def _mock_value(seed: str, metric_name: str) -> float:
    digest = hashlib.sha256(f"{seed}|{metric_name}".encode("utf-8")).hexdigest()
    number = int(digest[:8], 16)
    return float(100_000 + number % 900_000)
