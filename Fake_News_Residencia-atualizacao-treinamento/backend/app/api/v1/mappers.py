from app.domain.enums import IndicatorCode
from app.domain.models import AnalysisInput, AnalysisResult
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, Indicator

# Apresentação: textos mostrados ao usuário. Saem da API no PR 5.
INDICATOR_DESCRIPTIONS = {
    IndicatorCode.TRUSTED_DOMAIN: (
        "O domínio está na lista de fontes confiáveis. "
        "Isso não determina a veracidade do conteúdo porém indica uma fonte mais credível."
    ),
}


def to_input(request: AnalyzeRequest) -> AnalysisInput:
    # Só texto e URL entram na análise. O campo 'domain' é ignorado de propósito:
    # quem informa é o cliente, e ele poderia ser forjado.
    url = str(request.url) if request.url else None
    return AnalysisInput(text=request.text, url=url)


def to_response(result: AnalysisResult) -> AnalyzeResponse:
    return AnalyzeResponse(
        status="ok",
        classification=result.classification,
        confidence=result.confidence,
        fake_probability=result.fake_probability,
        method=result.method,
        justifications=result.justifications,
        indicators=[
            Indicator(code=code, description=INDICATOR_DESCRIPTIONS[code])
            for code in result.indicators
        ],
    )
