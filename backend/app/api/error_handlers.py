import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import AnalysisUnavailableError, TextTooShortError
from app.schemas.analyze import AnalyzeResponse, ErrorCode, ErrorInfo

logger = logging.getLogger("fake_news_api")


def _error_response(code: ErrorCode, message: str) -> JSONResponse:
    # HTTP 200 de propósito: decisão do grupo, o erro viaja no corpo (campo status).
    body = AnalyzeResponse(status="error", error=ErrorInfo(code=code, message=message))
    return JSONResponse(status_code=200, content=body.model_dump(mode="json"))


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(TextTooShortError)
    async def handle_text_too_short(
        request: Request, exc: TextTooShortError
    ) -> JSONResponse:
        return _error_response(
            ErrorCode.TEXT_TOO_SHORT,
            "O texto é curto demais para análise. "
            f"Selecione um trecho com pelo menos {exc.minimum} caracteres.",
        )

    @app.exception_handler(AnalysisUnavailableError)
    async def handle_analysis_unavailable(
        request: Request, exc: AnalysisUnavailableError
    ) -> JSONResponse:
        return _error_response(
            ErrorCode.ANALYSIS_UNAVAILABLE,
            "A análise está indisponível no momento. Tente novamente em instantes.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # RNF04, RNF14: o log não guarda o corpo da requisição nem o texto analisado
        logger.exception("Erro inesperado em %s %s", request.method, request.url.path)

        body = AnalyzeResponse(
            status="error",
            error=ErrorInfo(
                code=ErrorCode.INTERNAL_ERROR,
                message="Ocorreu um erro interno. Tente novamente em instantes.",
            ),
        )
        return JSONResponse(status_code=500, content=body.model_dump(mode="json"))