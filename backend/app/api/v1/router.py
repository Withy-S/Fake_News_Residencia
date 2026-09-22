from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_pipeline
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.pipeline import AnalysisPipeline

api_router = APIRouter()

PipelineDep = Annotated[AnalysisPipeline, Depends(get_pipeline)]


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, pipeline: PipelineDep) -> AnalyzeResponse:
    return pipeline.analyze(request)
