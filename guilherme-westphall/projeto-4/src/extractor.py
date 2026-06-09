import hashlib
import os
from pathlib import Path
from sqlite3 import Row

from .models import ExtractedMetric, ExtractionResult
from .schemas import DocumentExtraction


class MockLLMExtractor:
    name = "mock-llm-v1"

    def extract(self, document: Row, document_text: str | None = None) -> ExtractionResult:
        company = document["company"]
        year = document["year"]
        quarter = document["quarter"]
        seed = f"{company}|{year}|{quarter}|{document['document_url']}"

        parsed = DocumentExtraction(
            company=company,
            year=year,
            quarter=quarter,
            metrics=[
                {
                    "metric_name": "lancamentos",
                    "value": _mock_value(seed, "lancamentos"),
                    "unit": "R$ mil",
                    "confidence": "mock",
                    "evidence": "Valor simulado para validar contrato e persistencia.",
                },
                {
                    "metric_name": "vendas",
                    "value": _mock_value(seed, "vendas"),
                    "unit": "R$ mil",
                    "confidence": "mock",
                    "evidence": "Valor simulado para validar contrato e persistencia.",
                },
            ],
        )
        return extraction_from_schema(parsed, self.name)


class GeminiLLMExtractor:
    name = "gemini-2.5-flash"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        prompt_path: Path | None = None,
        max_chars: int = 30000,
        load_env: bool = True,
    ):
        self.name = model
        self.model = model
        self.prompt_path = prompt_path or Path(__file__).resolve().parents[1] / "prompts" / "extraction_prompt.md"
        self.max_chars = max_chars
        self.load_env = load_env

    def extract(self, document: Row, document_text: str | None = None) -> ExtractionResult:
        if not document_text:
            raise ValueError("Texto do documento e obrigatorio para extracao com Gemini.")

        try:
            from dotenv import load_dotenv
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Dependencias do Gemini ausentes. Rode `pip install -r requirements.txt`.") from exc

        if self.load_env:
            load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY nao encontrada. Adicione a chave ao arquivo .env.")

        prompt = self._build_prompt(document, document_text)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DocumentExtraction,
            ),
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, DocumentExtraction):
            return extraction_from_schema(parsed, self.name)
        if parsed is not None:
            return extraction_from_schema(DocumentExtraction.model_validate(parsed), self.name)

        return extraction_from_schema(DocumentExtraction.model_validate_json(response.text), self.name)

    def _build_prompt(self, document: Row, document_text: str) -> str:
        base_prompt = self.prompt_path.read_text(encoding="utf-8")
        text = document_text
        truncation_notice = ""
        if len(text) > self.max_chars:
            text = text[: self.max_chars]
            truncation_notice = "\nAviso: o texto foi truncado por limite de tamanho. Use confidence low se a evidencia estiver incompleta.\n"

        return f"""{base_prompt}

Contexto do documento:
- empresa: {document["company"]}
- ano: {document["year"]}
- trimestre: {document["quarter"]}
- titulo: {document["document_title"]}

{truncation_notice}
Texto do PDF:
{text}
"""


def extraction_from_schema(parsed: DocumentExtraction, extractor_name: str) -> ExtractionResult:
    return ExtractionResult(
        company=parsed.company,
        year=parsed.year,
        quarter=parsed.quarter,
        extractor_name=extractor_name,
        metrics=[
            ExtractedMetric(
                metric_name=metric.metric_name,
                value=metric.value,
                unit=metric.unit,
                confidence=metric.confidence,
                evidence=metric.evidence,
            )
            for metric in parsed.metrics
        ],
    )


def _mock_value(seed: str, metric_name: str) -> float:
    digest = hashlib.sha256(f"{seed}|{metric_name}".encode("utf-8")).hexdigest()
    number = int(digest[:8], 16)
    return float(100_000 + number % 900_000)
