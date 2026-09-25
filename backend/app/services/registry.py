import logging
from collections.abc import Callable

from app.core.config import Settings
from app.services.classifiers import AnalysisUnavailableError, Classifier
from app.services.resilience import ResilientClassifier

logger = logging.getLogger("fake_news_api")

ClassifierFactory = Callable[[Settings], Classifier]

_FACTORIES: dict[str, ClassifierFactory] = {}
_RESILIENT: dict[str, bool] = {}


def register(
    name: str, *, resilient: bool = True
) -> Callable[[ClassifierFactory], ClassifierFactory]:
    """Cadastra uma fábrica de classificador com um nome usado no .env.

    resilient=True envolve o classificador com timeout e isolamento de erro.
    """

    def decorator(factory: ClassifierFactory) -> ClassifierFactory:
        if name in _FACTORIES:
            raise ValueError(f"Classificador '{name}' registrado duas vezes.")
        _FACTORIES[name] = factory
        _RESILIENT[name] = resilient
        return factory

    return decorator


def available() -> list[str]:
    return sorted(_FACTORIES)


class UnavailableClassifier:
    """Ocupa o lugar de um classificador que não conseguiu carregar (RNF09)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def classify(self, text: str):
        raise AnalysisUnavailableError(f"Classificador '{self.name}' indisponível.")


def build(name: str, settings: Settings) -> Classifier:
    """Cria o classificador pelo nome.

    Nome desconhecido é erro de configuração: falha na hora (fail fast).
    Falha ao carregar (modelo ausente, dependência faltando) não derruba a API:
    o classificador vira indisponível e o pipeline segue o fluxo de fallback.
    """
    if name not in _FACTORIES:
        raise KeyError(f"Classificador '{name}' não existe. Disponíveis: {available()}")
    try:
        classifier = _FACTORIES[name](settings)
    except Exception:
        logger.exception("Falha ao carregar o classificador '%s'", name)
        return UnavailableClassifier(name)
    if _RESILIENT[name]:
        return ResilientClassifier(
            classifier, name, settings.classifier_timeout_seconds
        )
    return classifier
