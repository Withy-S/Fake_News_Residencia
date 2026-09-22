from app.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    Classification,
    ErrorCode,
    ErrorInfo,
    Method,
)
from app.services.classifiers import AnalysisUnavailableError, Classifier
from app.services.whitelist import is_trusted_domain


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

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        text = request.text.strip()

        if len(text) < self.min_text_length:
            return AnalyzeResponse(
                status="error",
                error=ErrorInfo(
                    code=ErrorCode.TEXT_TOO_SHORT,
                    message=(
                        "O texto é curto demais para análise. "
                        f"Selecione um trecho com pelo menos {self.min_text_length} caracteres."
                    ),
                ),
            )

        url = str(request.url) if request.url else None
        if is_trusted_domain(url, self.trusted_domains):
            return AnalyzeResponse(
                status="ok",
                classification=Classification.TRUSTED,
                method=Method.WHITELIST,
                justifications=["O domínio da página está na lista de fontes confiáveis."],
            )

        ml = self.classifier.classify(text)
        if ml.confidence >= self.min_confidence:
            return AnalyzeResponse(
                status="ok",
                classification=ml.classification,
                confidence=ml.confidence,
                method=Method.ML_MODEL,
                justifications=ml.justifications,
            )

        try:
            ai = self.fallback.classify(text)
        except AnalysisUnavailableError:
            return AnalyzeResponse(
                status="ok",
                classification=Classification.UNVERIFIED,
                confidence=ml.confidence,
                method=Method.ML_MODEL,
                justifications=[
                    "A confiança do modelo ficou abaixo do mínimo "
                    "e a análise complementar estava indisponível."
                ],
            )

        return AnalyzeResponse(
            status="ok",
            classification=ai.classification,
            confidence=ai.confidence,
            method=Method.AI_FALLBACK,
            justifications=ai.justifications,
        )