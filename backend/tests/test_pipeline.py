from app.schemas.analyze import AnalyzeRequest, Classification, ErrorCode, Method
from app.services.classifiers import (
    AnalysisUnavailableError,
    ClassifierResult,
    PlaceholderClassifier,
    UnavailableFallback,
)
from app.services.pipeline import AnalysisPipeline

TEXTO = "Texto longo o bastante para passar da validação de tamanho."


class FakeClassifier:
    """Classificador de mentira: devolve o resultado combinado e conta as chamadas."""

    def __init__(self, classification, confidence):
        self.result = ClassifierResult(
            classification, confidence, ["justificativa de teste"]
        )
        self.calls = 0

    def classify(self, text):
        self.calls += 1
        return self.result


class BrokenFallback:
    def classify(self, text):
        raise AnalysisUnavailableError("fora do ar")


def make_pipeline(classifier, fallback, trusted=None):
    return AnalysisPipeline(
        classifier=classifier,
        fallback=fallback,
        trusted_domains=trusted or [],
        min_confidence=0.6,
        min_text_length=20,
    )


def make_request(text=TEXTO, url=None, domain=None):
    return AnalyzeRequest(analysis_type="selecao", text=text, url=url, domain=domain)


def test_texto_curto_devolve_erro_sem_chamar_ninguem():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.9)
    resp = make_pipeline(ml, UnavailableFallback()).analyze(make_request(text="curto"))
    assert resp.status == "error"
    assert resp.error.code == ErrorCode.TEXT_TOO_SHORT
    assert ml.calls == 0


def test_dominio_da_whitelist_e_indicador_sem_substituir_o_modelo():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.9)
    pipeline = make_pipeline(ml, UnavailableFallback(), trusted=["gov.br"])
    resp = pipeline.analyze(make_request(url="https://saude.gov.br/noticia"))
    assert resp.classification == Classification.SUSPICIOUS
    assert resp.method == Method.ML_MODEL
    assert ml.calls == 1
    assert resp.indicators[0].code == "trusted_domain"


def test_campo_domain_forjado_nao_ativa_a_whitelist():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.9)
    pipeline = make_pipeline(ml, UnavailableFallback(), trusted=["gov.br"])
    resp = pipeline.analyze(make_request(url="https://evil.com/x", domain="gov.br"))
    assert resp.method == Method.ML_MODEL
    assert resp.classification == Classification.SUSPICIOUS


def test_modelo_confiante_nao_aciona_o_fallback():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.9)
    fallback = FakeClassifier(Classification.TRUSTED, 0.9)
    resp = make_pipeline(ml, fallback).analyze(make_request())
    assert resp.method == Method.ML_MODEL
    assert resp.confidence == 0.9
    assert fallback.calls == 0


def test_confianca_exatamente_no_minimo_conta_como_confiante():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.6)
    resp = make_pipeline(ml, UnavailableFallback()).analyze(make_request())
    assert resp.method == Method.ML_MODEL


def test_confianca_baixa_aciona_o_fallback():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.3)
    fallback = FakeClassifier(Classification.TRUSTED, 0.8)
    resp = make_pipeline(ml, fallback).analyze(make_request())
    assert resp.method == Method.AI_FALLBACK
    assert resp.classification == Classification.TRUSTED
    assert fallback.calls == 1


def test_fallback_indisponivel_devolve_nao_verificado_e_explica():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.3)
    resp = make_pipeline(ml, BrokenFallback()).analyze(make_request())
    assert resp.status == "ok"
    assert resp.classification == Classification.UNVERIFIED
    assert "indisponível" in resp.justifications[0]


def test_com_os_componentes_provisorios_o_resultado_e_nao_verificado():
    pipeline = make_pipeline(PlaceholderClassifier(), UnavailableFallback())
    resp = pipeline.analyze(make_request())
    assert resp.classification == Classification.UNVERIFIED


def test_indicador_preservado_no_fallback():
    ml = FakeClassifier(Classification.SUSPICIOUS, 0.3)
    fallback = FakeClassifier(Classification.UNVERIFIED, 0.5)
    resp = make_pipeline(ml, fallback, ["who.int"]).analyze(
        make_request(url="https://www.who.int/noticia")
    )
    assert resp.method == Method.AI_FALLBACK
    assert resp.classification == Classification.UNVERIFIED
    assert resp.indicators[0].code == "trusted_domain"
    assert fallback.calls == 1


def test_whitelist_nao_classifica_com_modelos_indisponiveis():
    resp = make_pipeline(
        PlaceholderClassifier(), UnavailableFallback(), ["who.int"]
    ).analyze(make_request(url="https://who.int/noticia"))
    assert resp.classification == Classification.UNVERIFIED
    assert resp.indicators[0].code == "trusted_domain"


def test_dominio_desconhecido_nao_gera_indicador_de_confianca():
    ml = FakeClassifier(Classification.UNVERIFIED, 0.8)
    resp = make_pipeline(ml, UnavailableFallback(), ["who.int"]).analyze(
        make_request(url="https://example.org/noticia")
    )
    assert resp.indicators == []
    assert resp.classification == Classification.UNVERIFIED
