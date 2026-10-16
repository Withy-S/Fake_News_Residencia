import pytest

import app.bootstrap.catalog  # noqa: F401
from app.adapters.classifiers import PlaceholderClassifier
from app.adapters.resilience import ResilientClassifier
from app.bootstrap.registry import UnavailableClassifier, available, build, register
from app.core.config import Settings
from app.domain.errors import AnalysisUnavailableError


def test_nomes_do_catalogo_estao_registrados():
    assert {"placeholder", "ai_fallback"} <= set(available())


def test_build_cria_pelo_nome_e_protege_com_timeout():
    clf = build("placeholder", Settings())
    assert isinstance(clf, ResilientClassifier)
    assert isinstance(clf.inner, PlaceholderClassifier)


def test_nome_desconhecido_falha_na_hora():
    with pytest.raises(KeyError, match="não existe"):
        build("nome_com_erro_de_digitacao", Settings())


def test_nome_repetido_e_recusado():
    with pytest.raises(ValueError, match="duas vezes"):
        register("placeholder")(lambda settings: None)


def test_falha_ao_carregar_vira_classificador_indisponivel():
    @register("teste_quebra_ao_carregar")
    def _quebra(settings):
        raise FileNotFoundError("modelo sumiu")

    clf = build("teste_quebra_ao_carregar", Settings())
    assert isinstance(clf, UnavailableClassifier)
    with pytest.raises(AnalysisUnavailableError):
        clf.classify("qualquer texto")
