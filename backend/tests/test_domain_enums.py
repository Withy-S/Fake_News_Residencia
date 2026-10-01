from app.domain import enums as domain_enums
from app.schemas import analyze as schemas


def test_valores_de_classification_sao_o_contrato():
    assert [c.value for c in domain_enums.Classification] == [
        "confiavel",
        "suspeito",
        "nao_verificado",
    ]


def test_valores_de_method_sao_o_contrato():
    assert [m.value for m in domain_enums.Method] == [
        "whitelist",
        "ml_model",
        "ai_fallback",
        "analise_linguistica",
    ]


def test_schemas_reexporta_o_mesmo_objeto():
    assert schemas.Classification is domain_enums.Classification
    assert schemas.Method is domain_enums.Method
