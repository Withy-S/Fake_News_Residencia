from dataclasses import dataclass, field

from app.domain.enums import Classification, IndicatorCode, Method


@dataclass(frozen=True)
class ClassifierResult:
    classification: Classification
    confidence: float
    justifications: list[str] = field(default_factory=list)
    method: Method = Method.ML_MODEL  # RF14: quem produziu o resultado


@dataclass(frozen=True)
class AnalysisInput:
    text: str
    url: str | None = None


@dataclass(frozen=True)
class AnalysisResult:
    classification: Classification
    confidence: float
    method: Method
    justifications: list[str] = field(default_factory=list)
    indicators: list[IndicatorCode] = field(default_factory=list)