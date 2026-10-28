"""Learnora API entry point.

Run locally with:
    uvicorn app.main:app --reload --port 8000
"""

import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .db import engine
from .routers import (
    admin,
    attempts,
    auth,
    learning,
    me,
    progress,
    purchases,
    subscription,
    wallet,
)

API_PREFIX = "/api/v1"

logger = logging.getLogger("learnora.api")


def _validation_message(exc: RequestValidationError) -> str:
    """Turn FastAPI's nested validation errors into one human-readable sentence."""
    problems: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
        message = str(error.get("msg", "is not valid")).removeprefix("Value error, ")
        problems.append(f"{location}: {message}" if location else message)
    if not problems:
        return "Some of the details you sent are not valid."
    return " ".join(problems)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    summary="Learn practical skills, pass assessments, earn rewards.",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": _validation_message(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log the traceback, answer the caller with the usual `{"detail": ...}` shape.

    Without this, an unexpected failure reaches the browser as a bare 500 that
    the frontend cannot explain. The traceback stays in the server logs.
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side. Please try again."},
    )


api = APIRouter(prefix=API_PREFIX)
api.include_router(auth.router)
api.include_router(me.router)
api.include_router(learning.router)
api.include_router(progress.router)
api.include_router(purchases.router)
api.include_router(subscription.router)
api.include_router(wallet.router)
api.include_router(attempts.router)
api.include_router(admin.router)


@api.get("/health", tags=["meta"], summary="Liveness probe")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "env": settings.env,
        "database": engine.url.get_backend_name(),
        "rewards_enabled": settings.rewards_enabled,
    }


@api.get("/health/ready", tags=["meta"], summary="Readiness probe")
def readiness() -> JSONResponse:
    """Prove the process can serve traffic, including reaching the database.

    Orchestrators and the container healthcheck poll this: a restarting
    PostgreSQL should take the API out of rotation instead of serving 500s.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Readiness check failed: the database is unreachable", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "down"},
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready", "env": settings.env, "database": "up"},
    )


app.include_router(api)
