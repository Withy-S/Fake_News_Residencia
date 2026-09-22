import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.analyze import AnalyzeResponse, ErrorCode, ErrorInfo

logger = logging.getLogger("fake_news_api")


def register_error_handlers(app: FastAPI) -> None:
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
