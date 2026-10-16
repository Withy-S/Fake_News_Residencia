from app.adapters.classifiers import UnavailableFallback
from app.adapters.heuristic import LinguisticClassifier
from app.application.pipeline import AnalysisPipeline
from app.domain.enums import Classification, Method
from app.domain.models import AnalysisInput

ALARMISTA = "URGENTE!!! COMPARTILHE antes que apaguem, a mídia não mostra ISSO!!"
NEUTRO = "Segundo o IBGE, a inflação de agosto ficou dentro da meta prevista."


def test_texto_alarmista_e_suspeito_com_justificativas():
    r = LinguisticClassifier().classify(ALARMISTA)
    assert r.classification == Classification.SUSPICIOUS
    assert r.confidence >= 0.5
    assert r.method == Method.LINGUISTIC
    assert any("sensacionalista" in j for j in r.justifications)


def test_texto_neutro_nao_vira_confiavel():
    r = LinguisticClassifier().classify(NEUTRO)
    assert r.classification == Classification.UNVERIFIED
    assert r.confidence == 0.0


def test_pipeline_informa_o_metodo_linguistico():
    pipeline = AnalysisPipeline(
        classifier=LinguisticClassifier(),
        fallback=UnavailableFallback(),
        trusted_domains=[],
        min_confidence=0.6,
        min_text_length=20,
    )
    resp = pipeline.analyze(AnalysisInput(text=ALARMISTA))
    assert resp.method == Method.LINGUISTIC
    assert resp.classification == Classification.SUSPICIOUS
