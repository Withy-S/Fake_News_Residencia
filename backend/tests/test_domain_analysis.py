import dataclasses

import pytest

from app.domain.enums import Classification, IndicatorCode, Method
from app.domain.errors import TextTooShortError
from app.domain.models import AnalysisInput, AnalysisResult


def test_codigo_do_indicador_e_o_contrato():
    assert IndicatorCode.TRUSTED_DOMAIN == "trusted_domain"


def test_texto_curto_carrega_o_minimo():
    assert TextTooShortError(20).minimum == 20


def test_resultado_e_imutavel_e_comeca_sem_indicadores():
    resultado = AnalysisResult(Classification.UNVERIFIED, 0.0, Method.ML_MODEL)
    assert resultado.indicators == []
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.confidence = 1.0


def test_entrada_sem_url_comeca_com_url_vazia():
    assert AnalysisInput(text="x").url is None
