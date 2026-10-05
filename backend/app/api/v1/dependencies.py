from functools import lru_cache

import app.bootstrap.catalog  # noqa: F401  (executa os @register)
from app.application.pipeline import AnalysisPipeline
from app.bootstrap.registry import build
from app.core.config import settings


@lru_cache
def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(
        classifier=build(settings.classifier, settings),
        fallback=build(settings.fallback_method, settings),
        trusted_domains=settings.trusted_domains,
        min_confidence=settings.min_confidence,
        min_text_length=settings.min_text_length,
    )
