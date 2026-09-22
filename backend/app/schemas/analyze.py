from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class AnalysisType(StrEnum):
    SELECTION = "selecao"  # RF02
    FULL_PAGE = "pagina_completa"  # RF03


class Classification(StrEnum):
    TRUSTED = "confiavel"
    SUSPICIOUS = "suspeito"
    UNVERIFIED = "nao_verificado"


class Method(StrEnum):
    WHITELIST = "whitelist"
    ML_MODEL = "ml_model"
    AI_FALLBACK = "ai_fallback"


class ErrorCode(StrEnum):
    TEXT_TOO_SHORT = "texto_insuficiente"  # RF23
    ANALYSIS_UNAVAILABLE = "analise_indisponivel"  # RF22, RNF09
    INTERNAL_ERROR = "erro_interno"  # RNF10


class AnalyzeRequest(BaseModel):
    analysis_type: AnalysisType
    text: str = Field(max_length=20_000)
    title: str | None = Field(default=None, max_length=500)
    url: HttpUrl | None = None
    domain: str | None = Field(default=None, max_length=255)


class Indicator(BaseModel):  # RF19 (V2)
    code: str
    description: str


class Source(BaseModel):  # RF09 e RF20 (V2)
    title: str
    url: HttpUrl


class ErrorInfo(BaseModel):
    code: ErrorCode
    message: str


class AnalyzeResponse(BaseModel):
    status: Literal["ok", "error"]
    classification: Classification | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    method: Method | None = None
    justifications: list[str] = []
    indicators: list[Indicator] = []
    sources: list[Source] = []
    error: ErrorInfo | None = None
    disclaimer: str = (
        "Classificação automática, sujeita a erros. "
        "Não é uma verificação de fatos: pesquise em fontes confiáveis."
    )
