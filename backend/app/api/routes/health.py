import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api.deps import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str


@router.get("", response_model=HealthResponse, summary="Application health")
async def health() -> HealthResponse:
    """Return process liveness without requiring a database connection."""
    return HealthResponse(status="ok")


@router.get("/db", response_model=DatabaseHealthResponse, summary="Database health")
async def database_health(
    session: AsyncSession = Depends(get_db),
) -> DatabaseHealthResponse | JSONResponse:
    """Execute a lightweight query and report actual database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError):
        # Keep database details in server logs only; the response is intentionally safe.
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "disconnected"},
        )
    return DatabaseHealthResponse(status="ok", database="connected")
