from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.error_handlers import register_error_handlers
from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Fake News Extension API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(api_router, prefix="/api/v1")
    register_error_handlers(app)
    # RNF: observabilidade. Expõe /metrics (latência, status, contagem por rota)
    # para o Prometheus coletar (ver docker-compose.yml e monitoring/).
    Instrumentator().instrument(app).expose(app)
    return app


app = create_app()
