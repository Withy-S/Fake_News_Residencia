import pytest
from pydantic import ValidationError

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, Classification


def test_request_minimo_e_valido():
    req = AnalyzeRequest(analysis_type="selecao", text="texto qualquer")
    assert req.url is None


def test_request_rejeita_tipo_desconhecido():
    with pytest.raises(ValidationError):
        AnalyzeRequest(analysis_type="imagem", text="x")


def test_response_sempre_traz_disclaimer():
    resp = AnalyzeResponse(status="ok", classification=Classification.UNVERIFIED)
    assert "sujeita a erros" in resp.disclaimer


def test_response_rejeita_confianca_fora_do_intervalo():
    with pytest.raises(ValidationError):
        AnalyzeResponse(status="ok", confidence=1.5)
