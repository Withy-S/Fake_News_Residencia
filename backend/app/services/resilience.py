import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from app.services.classifiers import (
    AnalysisUnavailableError,
    Classifier,
    ClassifierResult,
)

logger = logging.getLogger("fake_news_api")

# Pool compartilhado: cada análise roda numa thread separada para poder ter timeout.
_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="classifier")


class ResilientClassifier:
    """Envolve qualquer classificador com timeout e isolamento de erro (Decorator).

    Qualquer falha vira AnalysisUnavailableError, que o pipeline já sabe tratar.
    Limitação: o Python não consegue matar uma thread; após o timeout, a análise
    lenta continua rodando em segundo plano até terminar.
    """

    def __init__(self, inner: Classifier, name: str, timeout_seconds: float) -> None:
        self.inner = inner
        self.name = name
        self.timeout_seconds = timeout_seconds

    def classify(self, text: str) -> ClassifierResult:
        future = _POOL.submit(self.inner.classify, text)
        try:
            return future.result(timeout=self.timeout_seconds)
        except FutureTimeout:
            logger.warning("Classificador '%s' excedeu o timeout", self.name)
            raise AnalysisUnavailableError(f"'{self.name}' demorou demais.") from None
        except AnalysisUnavailableError:
            raise
        except Exception as exc:
            # RNF14: registra o tipo do erro, nunca o texto analisado.
            logger.error("Classificador '%s' falhou: %s", self.name, type(exc).__name__)
            raise AnalysisUnavailableError(f"'{self.name}' falhou.") from exc
