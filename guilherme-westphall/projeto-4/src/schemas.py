from typing import Literal

from pydantic import BaseModel, Field


MetricName = Literal["lancamentos", "vendas"]
Confidence = Literal["high", "medium", "low", "mock"]


class MetricExtraction(BaseModel):
    metric_name: MetricName = Field(description="Nome da metrica extraida.")
    value: float | None = Field(description="Valor absoluto extraido. Use null quando ausente.")
    unit: str = Field(description="Unidade do valor, por exemplo R$ mil, unidades ou %.")
    confidence: Confidence = Field(description="Confianca na extracao.")
    evidence: str | None = Field(default=None, description="Trecho curto do PDF usado como evidencia.")


class DocumentExtraction(BaseModel):
    company: str = Field(description="Empresa do documento.")
    year: int | None = Field(description="Ano de referencia.")
    quarter: int | None = Field(description="Trimestre de referencia entre 1 e 4.")
    metrics: list[MetricExtraction] = Field(description="Metricas extraidas do documento.")
