import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_pipeline
from app.domain.enums import Classification
from app.domain.errors import AnalysisUnavailableError
from app.domain.models import ClassifierResult
from app.main import app
from app.services.pipeline import AnalysisPipeline

GOLDEN = Path(__file__).parent / "golden" / "analyze_responses.json"
TEXTO = "Texto longo o bastante para passar da validação de tamanho."
S, T, U = Classification.SUSPICIOUS, Classification.TRUSTED, Classification.UNVERIFIED

client = TestClient(app)


class Fake:
    def __init__(self, classification, confidence):
        self.result = ClassifierResult(
            classification, confidence, ["justificativa de teste"]
        )

    def classify(self, text):
        return self.result


class Broken:
    def classify(self, text):
        raise AnalysisUnavailableError("fora do ar")


def make_pipeline(ml, fallback, trusted=()):
    return AnalysisPipeline(
        classifier=ml,
        fallback=fallback,
        trusted_domains=list(trusted),
        min_confidence=0.6,
        min_text_length=20,
    )


CASOS = {
    "texto_curto": (
        lambda: make_pipeline(Fake(S, 0.9), Broken()),
        {"text": "curto"},
    ),
    "ml_confiante": (
        lambda: make_pipeline(Fake(S, 0.9), Broken()),
        {"text": TEXTO},
    ),
    "indicador_whitelist": (
        lambda: make_pipeline(Fake(S, 0.9), Broken(), ["gov.br"]),
        {"text": TEXTO, "url": "https://saude.gov.br/noticia"},
    ),
    "fallback_acionado": (
        lambda: make_pipeline(Fake(S, 0.3), Fake(T, 0.8)),
        {"text": TEXTO},
    ),
    "fallback_indisponivel": (
        lambda: make_pipeline(Fake(S, 0.3), Broken()),
        {"text": TEXTO},
    ),
    "tudo_indisponivel": (
        lambda: make_pipeline(Broken(), Broken()),
        {"text": TEXTO},
    ),
    "indicador_no_fallback": (
        lambda: make_pipeline(Fake(S, 0.3), Fake(U, 0.5), ["who.int"]),
        {"text": TEXTO, "url": "https://www.who.int/noticia"},
    ),
}


def run_case(nome):
    build, corpo = CASOS[nome]
    app.dependency_overrides[get_pipeline] = build
    try:
        resposta = client.post(
            "/api/v1/analyze", json={"analysis_type": "selecao", **corpo}
        )
    finally:
        app.dependency_overrides.clear()
    return {"http": resposta.status_code, "json": resposta.json()}


@pytest.mark.skipif(
    os.environ.get("UPDATE_GOLDEN") != "1",
    reason="só roda ao atualizar o golden de propósito",
)
def test_regenera_o_golden():
    atual = {nome: run_case(nome) for nome in CASOS}
    conteudo = json.dumps(atual, indent=2, sort_keys=True, ensure_ascii=False)
    GOLDEN.write_text(conteudo + "\n", encoding="utf-8")


@pytest.mark.parametrize("nome", list(CASOS))
def test_resposta_da_api_continua_igual(nome):
    esperado = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert run_case(nome) == esperado[nome]
