from dataclasses import dataclass, field

from app.domain.enums import Classification, Method


@dataclass(frozen=True)
class ClassifierResult:
    classification: Classification
    confidence: float
    justifications: list[str] = field(default_factory=list)
    method: Method = Method.ML_MODEL  # RF14: quem produziu o resultado
