from app.domain.enums import Classification
from app.domain.errors import AnalysisUnavailableError
from app.domain.models import ClassifierResult


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