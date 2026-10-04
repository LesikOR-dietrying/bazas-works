from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.engine import Engine

from app.core.database import get_engine
from app.services.health import DatabaseNotReady, verify_database

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=HealthResponse)
def readiness(engine: Annotated[Engine, Depends(get_engine)]) -> HealthResponse:
    try:
        verify_database(engine)
    except DatabaseNotReady:
        raise HTTPException(status_code=503, detail="Database is not ready") from None
    return HealthResponse()
