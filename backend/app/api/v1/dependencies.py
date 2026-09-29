from functools import lru_cache

import app.services.catalog  # noqa: F401  (executa os @register)
from app.core.config import settings
from app.services.pipeline import AnalysisPipeline
from app.services.registry import build


@lru_cache
def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(
        classifier=build(settings.classifier, settings),
        fallback=build(settings.fallback_method, settings),
        trusted_domains=settings.trusted_domains,
        min_confidence=settings.min_confidence,
        min_text_length=settings.min_text_length,
    )
