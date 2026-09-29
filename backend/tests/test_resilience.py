import time

import pytest

from app.schemas.analyze import Classification
from app.services.classifiers import AnalysisUnavailableError, ClassifierResult
from app.services.resilience import ResilientClassifier


class Rapido:
    def classify(self, text):
        return ClassifierResult(Classification.SUSPICIOUS, 0.9)


class Lento:
    def classify(self, text):
        time.sleep(0.5)
        return ClassifierResult(Classification.SUSPICIOUS, 0.9)


class ComBug:
    def classify(self, text):
        raise ZeroDivisionError("bug no classificador")


def test_resultado_normal_passa_direto():
    r = ResilientClassifier(Rapido(), "rapido", 1.0).classify("texto")
    assert r.confidence == 0.9


def test_timeout_vira_indisponivel():
    with pytest.raises(AnalysisUnavailableError, match="demorou"):
        ResilientClassifier(Lento(), "lento", 0.1).classify("texto")


def test_bug_vira_indisponivel():
    with pytest.raises(AnalysisUnavailableError, match="falhou"):
        ResilientClassifier(ComBug(), "com_bug", 1.0).classify("texto")
