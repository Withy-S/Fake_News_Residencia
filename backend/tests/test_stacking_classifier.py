import numpy as np
import pytest

from app.adapters.stacking_classifier import StackingClassifier
from app.domain.enums import Classification, Method

# Amostras em português natural, tiradas do Fake.br (rótulo conhecido). O modelo foi treinado
# também com metade dos pares do Fake.br; estes testes verificam o artefato e a integração,
# não a capacidade de generalizar para fontes novas.
AMOSTRA_REAL = 'temer diz estar aberto ao diálogo com parlamentares para aprovar reforma da previdência. em entrevista à tv bandeirantes, o presidente michel temer admitiu que aceitaria outras modificações ao projeto formatado pelo governo federal para que o texto seja aprovado no congresso.. o presidente michel temer afirmou, em entrevista à tv bandeirantes transmitida na noite desta terça-feira (6), que o governo está aberto ao diálogo para conseguir aprovar a reforma da previdência neste mês. "o governo está aberto ao diálogo e evidentemente os parlamentares estão abertos ao diálogo", afirmou ele. "nesse projeto que está formatado agora, a economia é entre r$'
AMOSTRA_FAKE = 'peixe morre pela boca: "se continuarem as delações, nenhum de nós escapa". . lula sendo lula: "eu quero que qualquer pessoa que tenha roubado seja preso [...] é importante deixar claro [...] mais eu quero que toda e qualquer pessoa, do mais pobre ao mais rico tenha um julgamento tenha um julgamento democrático. ninguém pode ser preso por uma delação premiada, porque se isso continuar nenhum de nós escapa" em março deste ano, lula já havia deixado escapar outra besteira ... quando discursava em um congresso de professores em serra negra ( sp ) na época, ele disse que o'


@pytest.fixture(scope="module")
def classificador():
    return StackingClassifier("models/stacking.joblib")


def test_acerta_amostra_real_em_portugues_natural(classificador):
    resultado = classificador.classify(AMOSTRA_REAL)
    assert resultado.fake_probability < 0.3
    assert resultado.classification != Classification.SUSPICIOUS


def test_acerta_amostra_fake_em_portugues_natural(classificador):
    resultado = classificador.classify(AMOSTRA_FAKE)
    assert resultado.classification == Classification.SUSPICIOUS
    assert resultado.fake_probability >= 0.7


def test_faixa_de_incerteza_nao_e_suspeito(classificador, monkeypatch):
    class MetaFixo:
        classes_ = np.array([0, 1])

        def predict_proba(self, _):
            return np.array([[0.5, 0.5]])

    monkeypatch.setattr(classificador, "meta_model", MetaFixo())
    resultado = classificador.classify(AMOSTRA_REAL)
    assert resultado.classification == Classification.UNVERIFIED
    assert any("incerteza" in j for j in resultado.justifications)


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
        Classification.UNVERIFIED,
    }
    assert result.justifications


def test_stacking_normaliza_sem_truncar_texto():
    classifier = StackingClassifier("models/stacking.joblib")
    text = "\ufeffNOTICIA none " + "PALAVRA " * 105
    prepared_text = "noticia " + "palavra " * 105

    probabilities = [
        float(model.predict_proba([prepared_text])[0, list(model.classes_).index(1)])
        for model in (classifier.models[name] for name in classifier.base_models)
    ]
    clipped = np.clip(probabilities, 1e-4, 1 - 1e-4)
    logits = np.log(clipped / (1 - clipped)).reshape(1, -1)
    expected = classifier.meta_model.predict_proba(logits)[0, 1]

    result = classifier.classify(text)

    assert np.isclose(result.fake_probability, expected)
