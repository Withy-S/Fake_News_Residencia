from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_pipeline
from app.api.v1.mappers import to_input, to_response
from app.application.pipeline import AnalysisPipeline
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse

api_router = APIRouter()

PipelineDep = Annotated[AnalysisPipeline, Depends(get_pipeline)]


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, pipeline: PipelineDep) -> AnalyzeResponse:
    return to_response(pipeline.analyze(to_input(request)))
