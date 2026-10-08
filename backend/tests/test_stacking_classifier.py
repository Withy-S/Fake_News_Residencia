from app.adapters.stacking_classifier import StackingClassifier
from app.domain.enums import Classification, Method


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
