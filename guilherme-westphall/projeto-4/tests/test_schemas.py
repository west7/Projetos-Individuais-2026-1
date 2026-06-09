import pytest
from pydantic import ValidationError

from src.schemas import DocumentExtraction


def test_document_extraction_accepts_null_value():
    parsed = DocumentExtraction.model_validate(
        {
            "company": "MRV",
            "year": 2026,
            "quarter": 1,
            "metrics": [
                {
                    "metric_name": "lancamentos",
                    "value": None,
                    "unit": "R$ mil",
                    "confidence": "low",
                    "evidence": None,
                }
            ],
        }
    )

    assert parsed.metrics[0].value is None


def test_document_extraction_rejects_unknown_metric():
    with pytest.raises(ValidationError):
        DocumentExtraction.model_validate(
            {
                "company": "MRV",
                "year": 2026,
                "quarter": 1,
                "metrics": [
                    {
                        "metric_name": "lucro",
                        "value": 1,
                        "unit": "R$ mil",
                        "confidence": "high",
                    }
                ],
            }
        )

