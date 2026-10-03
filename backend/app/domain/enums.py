"""Vocabulário do domínio: o que o sistema pode responder e quem respondeu."""

from enum import StrEnum


class Classification(StrEnum):
    TRUSTED = "confiavel"
    SUSPICIOUS = "suspeito"
    UNVERIFIED = "nao_verificado"


class Method(StrEnum):
    WHITELIST = "whitelist"
    ML_MODEL = "ml_model"
    AI_FALLBACK = "ai_fallback"
    LINGUISTIC = "analise_linguistica"  # RF07


class IndicatorCode(StrEnum):
    TRUSTED_DOMAIN = "trusted_domain"