import pytest

from app.adapters.stacking_classifier import StackingClassifier
from app.domain.enums import Classification, Method

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


@pytest.fixture(scope="module")
def classificador():
    return StackingClassifier("models/stacking.joblib")


def test_acerta_amostra_real_do_proprio_dataset_de_treino(classificador):
    resultado = classificador.classify(AMOSTRA_REAL_DATASET)
    assert resultado.fake_probability <= 0.1
    assert resultado.classification != Classification.SUSPICIOUS


def test_acerta_amostra_fake_do_proprio_dataset_de_treino(classificador):
    resultado = classificador.classify(AMOSTRA_FAKE_DATASET)
    assert resultado.classification == Classification.SUSPICIOUS
    assert resultado.fake_probability >= 0.9


def test_stacking_carrega_artefato_e_retorna_probabilidade_fake():
    classifier = StackingClassifier("models/stacking.joblib")
    result = classifier.classify(
        "Texto de notícia para análise automática com contexto e afirmações verificáveis."
    )

    assert 0 <= result.fake_probability <= 1
    assert result.confidence == max(
        result.fake_probability, 1 - result.fake_probability
    )
    assert result.method == Method.ML_MODEL
    assert result.classification in {
        Classification.SUSPICIOUS,
        Classification.TRUSTED,
        Classification.UNVERIFIED,
    }
    assert result.justifications
