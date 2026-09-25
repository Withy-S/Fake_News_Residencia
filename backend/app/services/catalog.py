"""Catálogo: liga cada nome do .env à classe que implementa o classificador.

Classificador novo? Crie a classe, registre a fábrica aqui e use o nome no .env.
"""

from app.core.config import Settings
from app.services.classifiers import PlaceholderClassifier, UnavailableFallback
from app.services.ensemble import EnsembleClassifier
from app.services.heuristic import LinguisticClassifier
from app.services.registry import build, register


@register("placeholder")
def _placeholder(settings: Settings) -> PlaceholderClassifier:
    return PlaceholderClassifier()


@register("ai_fallback")
def _ai_fallback(settings: Settings) -> UnavailableFallback:
    # Provisório até a análise por IA generativa existir (RF11).
    return UnavailableFallback()


@register("linguistico")
def _linguistico(settings: Settings) -> LinguisticClassifier:
    return LinguisticClassifier()


@register("combinado", resilient=False)  # cada membro já tem o próprio timeout
def _combinado(settings: Settings) -> EnsembleClassifier:
    members = {name: build(name, settings) for name in settings.ensemble_members}
    return EnsembleClassifier(members, settings.ensemble_weights)
