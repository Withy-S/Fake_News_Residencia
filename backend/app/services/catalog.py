"""Catálogo: liga cada nome do .env à classe que implementa o classificador.

Classificador novo? Crie a classe, registre a fábrica aqui e use o nome no .env.
"""

from app.core.config import Settings
from app.services.classifiers import PlaceholderClassifier, UnavailableFallback
from app.services.registry import register


@register("placeholder")
def _placeholder(settings: Settings) -> PlaceholderClassifier:
    return PlaceholderClassifier()


@register("ai_fallback")
def _ai_fallback(settings: Settings) -> UnavailableFallback:
    # Provisório até a análise por IA generativa existir (RF11).
    return UnavailableFallback()