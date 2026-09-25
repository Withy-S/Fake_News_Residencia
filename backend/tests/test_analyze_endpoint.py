from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_pipeline
from app.main import app
from app.schemas.analyze import Classification
from app.services.classifiers import ClassifierResult
from app.services.pipeline import AnalysisPipeline

client = TestClient(app)


class StubClassifier:
    def __init__(self, classification, confidence):
        self.classification = classification
        self.confidence = confidence

    def classify(self, text):
        return ClassifierResult(self.classification, self.confidence, ["stub"])


def override_pipeline(classification=Classification.SUSPICIOUS, confidence=0.9):
    pipeline = AnalysisPipeline(
        classifier=StubClassifier(classification, confidence),
        fallback=StubClassifier(Classification.TRUSTED, 0.9),
        trusted_domains=["gov.br"],
        min_confidence=0.6,
        min_text_length=20,
    )
    app.dependency_overrides[get_pipeline] = lambda: pipeline


def teardown_function():
    app.dependency_overrides.clear()


def test_analyze_devolve_classificacao():
    override_pipeline()
    response = client.post(
        "/api/v1/analyze",
        json={
            "analysis_type": "selecao",
            "text": "Um texto longo o suficiente para passar da validação.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["classification"] == "suspeito"
    assert body["method"] == "ml_model"
    assert "sujeita a erros" in body["disclaimer"]


def test_analyze_rejeita_texto_muito_curto():
    override_pipeline()
    response = client.post(
        "/api/v1/analyze",
        json={"analysis_type": "selecao", "text": "curto"},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "texto_insuficiente"


def test_analyze_rejeita_corpo_invalido():
    response = client.post(
        "/api/v1/analyze",
        json={"analysis_type": "tipo_que_nao_existe", "text": "algum texto"},
    )
    assert response.status_code == 422


def test_analyze_usa_whitelist():
    override_pipeline()
    response = client.post(
        "/api/v1/analyze",
        json={
            "analysis_type": "pagina_completa",
            "text": "Um texto longo o suficiente para passar da validação.",
            "url": "https://saude.gov.br/x",
        },
    )
    body = response.json()
    assert body["method"] == "ml_model"
    assert body["classification"] == "suspeito"
    assert body["indicators"][0]["code"] == "trusted_domain"
