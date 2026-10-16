from app.api.v1.mappers import to_input, to_response
from app.domain.enums import Classification, IndicatorCode, Method
from app.domain.models import AnalysisInput, AnalysisResult
from app.schemas.analyze import AnalyzeRequest

TEXTO = "Texto longo o bastante para passar da validação de tamanho."


def test_to_input_converte_a_url_para_texto():
    request = AnalyzeRequest(
        analysis_type="selecao", text=TEXTO, url="https://saude.gov.br/noticia"
    )
    assert to_input(request) == AnalysisInput(
        text=TEXTO, url="https://saude.gov.br/noticia"
    )


def test_to_input_ignora_o_campo_domain_forjado():
    request = AnalyzeRequest(
        analysis_type="selecao", text=TEXTO, url="https://evil.com/x", domain="gov.br"
    )
    assert to_input(request).url == "https://evil.com/x"


def test_to_response_traduz_indicador_em_descricao():
    result = AnalysisResult(
        Classification.SUSPICIOUS,
        0.9,
        Method.ML_MODEL,
        ["j"],
        [IndicatorCode.TRUSTED_DOMAIN],
    )
    response = to_response(result)
    assert response.status == "ok"
    assert response.indicators[0].code == "trusted_domain"
    assert "fontes confiáveis" in response.indicators[0].description
