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

# Amostras retiradas de dados_tratados/NoRemovalWords_tratada_dedup.csv (rótulo
# conhecido), já na forma lematizada que o FakeRecogna usa nativamente na coluna
# `Noticia` (ver "Limitação conhecida" em ml/README.md). Propositalmente NÃO é
# português natural: isso testa o modelo e os artefatos isolados do problema de
# pré-processamento do texto de entrada, que é um bug diferente e já documentado.
AMOSTRA_REAL_DATASET = (
    "dia noite acessório passar o código vestimenta pessoa mundo e d tênis chunky "
    "o bermuda ciclista permitir divisão acalorar opinião máscara chegar ficar e "
    "haver o tendência durar goste-se aliar importante prevenção o o coronavírus "
    "e obrigatório país chegar máscara centrar polêmicas o envolver o marcar "
    "osklen vender o item o o preço r$ o unidade e execrar redar social eua o "
    "empresário kim kardashian"
)
AMOSTRA_FAKE_DATASET = (
    "sucessivo falhar umar d atribuir diretamente o o gol santo vencer o vasco x "
    "o goleiro sidão acabar escolher popularmente e ironicamente comer o craque o "
    "término jogar umar repórter tv globo entregar troféu “ craque jogar ” o o "
    "goleiro visivelmente constranger conferir o abaixar"
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


def test_acerta_amostra_real_do_proprio_dataset_de_treino(classificador):
    resultado = classificador.classify(AMOSTRA_REAL_DATASET)
    assert resultado.classification == Classification.TRUSTED
    assert resultado.confidence >= 0.9


def test_acerta_amostra_fake_do_proprio_dataset_de_treino(classificador):
    resultado = classificador.classify(AMOSTRA_FAKE_DATASET)
    assert resultado.classification == Classification.SUSPICIOUS
    assert resultado.confidence >= 0.9
