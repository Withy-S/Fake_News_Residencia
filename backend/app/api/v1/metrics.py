"""Métricas de negócio do /analyze, para detectar deriva do modelo (RNF08).

Separado das métricas HTTP padrão (latência, status) que o
prometheus-fastapi-instrumentator já cobre em app/main.py.
"""

from prometheus_client import Counter, Histogram

from app.schemas.analyze import AnalyzeResponse

CLASSIFICATIONS = Counter(
    "fn_classifications_total",
    "Classificações retornadas pelo /analyze, por resultado e método",
    ["classification", "method"],
)

CONFIDENCE = Histogram(
    "fn_confidence",
    "Confiança retornada pelo /analyze, por método",
    ["method"],
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)


def registrar(response: AnalyzeResponse) -> None:
    """Registra uma resposta do /analyze nas métricas. Resposta de erro não conta."""
    if response.status != "ok" or response.classification is None:
        return
    method = response.method.value if response.method else "desconhecido"
    CLASSIFICATIONS.labels(classification=response.classification.value, method=method).inc()
    if response.confidence is not None:
        CONFIDENCE.labels(method=method).observe(response.confidence)
