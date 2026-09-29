from dataclasses import dataclass, field
from typing import Protocol

from app.schemas.analyze import Classification, Method


class AnalysisUnavailableError(Exception):
    """Um mecanismo de análise está fora do ar (RF22, RNF09)."""


@dataclass(frozen=True)
class ClassifierResult:
    classification: Classification
    confidence: float
    justifications: list[str] = field(default_factory=list)
    method: Method = Method.ML_MODEL  # RF14: quem produziu o resultado


class Classifier(Protocol):
    def classify(self, text: str) -> ClassifierResult: ...


class PlaceholderClassifier:
    """Provisório: o modelo de ML ainda não foi treinado. Nunca tem confiança."""

    def classify(self, text: str) -> ClassifierResult:
        return ClassifierResult(
            classification=Classification.UNVERIFIED,
            confidence=0.0,
            justifications=["O modelo de classificação ainda não está disponível."],
        )


class UnavailableFallback:
    """Provisório: a análise complementar por IA ainda não existe."""

    def classify(self, text: str) -> ClassifierResult:
        raise AnalysisUnavailableError("Análise complementar por IA indisponível.")
