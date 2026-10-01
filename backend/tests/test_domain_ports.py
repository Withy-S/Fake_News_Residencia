import dataclasses

import pytest

from app.domain import errors, models, ports
from app.domain.enums import Classification, Method
from app.services import classifiers


def test_resultado_usa_ml_como_metodo_padrao():
    resultado = models.ClassifierResult(Classification.UNVERIFIED, 0.0)
    assert resultado.method is Method.ML_MODEL


def test_resultado_e_imutavel():
    resultado = models.ClassifierResult(Classification.UNVERIFIED, 0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.confidence = 1.0


def test_services_reexporta_os_mesmos_objetos():
    assert classifiers.ClassifierResult is models.ClassifierResult
    assert classifiers.AnalysisUnavailableError is errors.AnalysisUnavailableError
    assert classifiers.Classifier is ports.Classifier
