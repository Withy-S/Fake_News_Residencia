from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_pipeline
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


class BrokenPipeline:
    def analyze(self, request):
        raise RuntimeError("falha simulada para teste")


def test_erro_inesperado_devolve_formato_padronizado():
    app.dependency_overrides[get_pipeline] = lambda: BrokenPipeline()
    try:
        response = client.post(
            "/api/v1/analyze",
            json={
                "analysis_type": "selecao",
                "text": "Um texto longo o suficiente para passar da validação.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "erro_interno"
    assert "falha simulada" not in body["error"]["message"]
