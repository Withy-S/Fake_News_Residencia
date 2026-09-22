from functools import lru_cache

from app.core.config import settings
from app.services.classifiers import PlaceholderClassifier, UnavailableFallback
from app.services.pipeline import AnalysisPipeline


@lru_cache
def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(
        classifier=PlaceholderClassifier(),
        fallback=UnavailableFallback(),
        trusted_domains=settings.trusted_domains,
        min_confidence=settings.min_confidence,
        min_text_length=settings.min_text_length,
    )
