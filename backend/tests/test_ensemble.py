import pytest

import app.services.catalog  # noqa: F401
from app.core.config import Settings
from app.schemas.analyze import Classification, Method
from app.services.classifiers import AnalysisUnavailableError, ClassifierResult
from app.services.ensemble import EnsembleClassifier
from app.services.registry import build


class Fixo:
    def __init__(self, classification, confidence, method=Method.ML_MODEL):
        self.result = ClassifierResult(classification, confidence, ["fixo"], method)

    def classify(self, text):
        return self.result


class Fora:
    def classify(self, text):
        raise AnalysisUnavailableError("fora do ar")


def test_vence_a_classificacao_com_mais_votos():
    ens = EnsembleClassifier(
        {
            "ml": Fixo(Classification.SUSPICIOUS, 0.9),
            "ling": Fixo(Classification.UNVERIFIED, 0.0, Method.LINGUISTIC),
        },
        weights={"ml": 3, "ling": 1},
    )
    r = ens.classify("texto")
    assert r.classification == Classification.SUSPICIOUS
    assert r.confidence == round(3 * 0.9 / 4, 2)
    assert r.method == Method.ML_MODEL


def test_membro_fora_do_ar_nao_vota():
    ens = EnsembleClassifier(
        {"ml": Fora(), "ling": Fixo(Classification.SUSPICIOUS, 0.8, Method.LINGUISTIC)},
        weights={},
    )
    r = ens.classify("texto")
    assert r.confidence == 0.8
    assert r.method == Method.LINGUISTIC


def test_todos_fora_do_ar_deixa_o_conjunto_indisponivel():
    ens = EnsembleClassifier({"a": Fora(), "b": Fora()}, weights={})
    with pytest.raises(AnalysisUnavailableError):
        ens.classify("texto")


def test_combinado_montado_pelo_env():
    s = Settings(
        classifier="combinado", ensemble_members=["linguistico", "placeholder"]
    )
    ens = build("combinado", s)
    assert isinstance(ens, EnsembleClassifier)
    assert list(ens.members) == ["linguistico", "placeholder"]
