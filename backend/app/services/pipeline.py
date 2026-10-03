from app.domain.enums import Classification, IndicatorCode, Method
from app.domain.errors import AnalysisUnavailableError, TextTooShortError
from app.domain.models import AnalysisInput, AnalysisResult
from app.domain.ports import Classifier
from app.services.trustlist import is_trusted_domain


class AnalysisPipeline:
    def __init__(
        self,
        *,
        classifier: Classifier,
        fallback: Classifier,
        trusted_domains: list[str],
        min_confidence: float,
        min_text_length: int,
    ) -> None:
        self.classifier = classifier
        self.fallback = fallback
        self.trusted_domains = trusted_domains
        self.min_confidence = min_confidence
        self.min_text_length = min_text_length

    def analyze(self, data: AnalysisInput) -> AnalysisResult:
        text = data.text.strip()

        if len(text) < self.min_text_length:
            raise TextTooShortError(self.min_text_length)

        indicators = []
        if is_trusted_domain(data.url, self.trusted_domains):
            indicators.append(IndicatorCode.TRUSTED_DOMAIN)

        try:
            ml = self.classifier.classify(text)
        except AnalysisUnavailableError:
            ml = None  # RNF09: segue para o fallback em vez de quebrar

        if ml is not None and ml.confidence >= self.min_confidence:
            return AnalysisResult(
                classification=ml.classification,
                confidence=ml.confidence,
                method=ml.method,
                justifications=ml.justifications,
                indicators=indicators,
            )

        try:
            ai = self.fallback.classify(text)
        except AnalysisUnavailableError:
            if ml is None:
                # Nenhum mecanismo analisou o texto: é falha, não resultado (RF21).
                raise
            return AnalysisResult(
                classification=Classification.UNVERIFIED,
                confidence=ml.confidence,
                method=ml.method,
                justifications=[
                    (
                        "A confiança do modelo ficou abaixo do mínimo "
                        "e a análise complementar estava indisponível."
                    )
                ],
                indicators=indicators,
            )

        return AnalysisResult(
            classification=ai.classification,
            confidence=ai.confidence,
            method=Method.AI_FALLBACK,
            justifications=ai.justifications,
            indicators=indicators,
        )