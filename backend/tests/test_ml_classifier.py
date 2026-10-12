import pytest

from app.domain.enums import Classification, Method
from app.domain.models import ClassifierResult

NEUTRO = (
    "O Banco Central manteve a taxa Selic em reunião realizada nesta quarta-feira, "
    "conforme comunicado divulgado pelo Copom e amplamente noticiado pela imprensa."
)
SENSACIONALISTA = (
    "URGENTE!!! COMPARTILHE AGORA antes que apaguem: a mídia esconde isso de você, "
    "cientistas escondem a cura definitiva e ninguém está falando sobre o escândalo!!!"
)


def _carregar_classificador():
    try:
        from app.adapters.ml_classifier import MLStackingClassifier
    except ImportError as exc:
        pytest.skip(f"Dependências de ML não instaladas: {exc}")
    try:
        return MLStackingClassifier()
    except FileNotFoundError as exc:
        pytest.skip(
            f"Artefatos de ML ausentes (rode ml/treinar_e_exportar_stacking.py): {exc}"
        )
    except Exception as exc:  # noqa: BLE001 (sem internet, HF indisponível, etc.: pular, não quebrar)
        pytest.skip(f"Não foi possível carregar o MLStackingClassifier: {exc}")


@pytest.fixture(scope="module")
def classificador():
    return _carregar_classificador()


@pytest.mark.parametrize("texto", [NEUTRO, SENSACIONALISTA])
def test_classifica_respeitando_o_contrato(classificador, texto):
    resultado = classificador.classify(texto)
    assert isinstance(resultado, ClassifierResult)
    assert resultado.classification in Classification
    assert 0.0 <= resultado.confidence <= 1.0
    assert resultado.method == Method.ML_MODEL
    assert resultado.justifications


def test_dois_textos_diferentes_nao_quebram_o_estado_interno(classificador):
    r1 = classificador.classify(NEUTRO)
    r2 = classificador.classify(SENSACIONALISTA)
    assert isinstance(r1, ClassifierResult)
    assert isinstance(r2, ClassifierResult)
