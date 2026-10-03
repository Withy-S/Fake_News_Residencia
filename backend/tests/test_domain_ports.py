import dataclasses

import pytest

from app.domain import models
from app.domain.enums import Classification, Method


def test_resultado_usa_ml_como_metodo_padrao():
    resultado = models.ClassifierResult(Classification.UNVERIFIED, 0.0)
    assert resultado.method is Method.ML_MODEL


def test_resultado_e_imutavel():
    resultado = models.ClassifierResult(Classification.UNVERIFIED, 0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.confidence = 1.0
