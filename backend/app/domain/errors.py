class AnalysisUnavailableError(Exception):
    """Um mecanismo de análise está fora do ar (RF22, RNF09)."""
class AnalysisUnavailableError(Exception):
    """Um mecanismo de análise está fora do ar (RF22, RNF09)."""


class TextTooShortError(Exception):
    """O texto não atinge o tamanho mínimo para análise (RF23)."""

    def __init__(self, minimum: int) -> None:
        super().__init__(f"Texto abaixo do mínimo de {minimum} caracteres.")
        self.minimum = minimum