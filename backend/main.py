"""UNTrade FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import BusinessRuleError, close_pool, init_pool
from routers import admin as admin_router
from routers import auth as auth_router
from routers import catalog as catalog_router
from routers import seller as seller_router
from routers import transactions as transactions_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        await init_pool()
    except Exception as exc:
        raise RuntimeError(f"Database startup failed: {exc}") from exc
    try:
        yield
    finally:
        await close_pool()


settings = get_settings()

app = FastAPI(
    title="UNTrade API",
    description=(
        "University Exchange & Marketplace Platform. "
        "Talks to MySQL 8.4 `UnTrade` via raw SQL, CALL procedures, and views."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessRuleError)
async def business_rule_exception_handler(
    _request: Request,
    exc: BusinessRuleError,
) -> JSONResponse:
    """Map MySQL SIGNAL SQLSTATE '45000' (triggers/procedures) → HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )


API_PREFIX = "/api/v1"
app.include_router(auth_router.router, prefix=API_PREFIX)
app.include_router(catalog_router.router, prefix=API_PREFIX)
app.include_router(transactions_router.router, prefix=API_PREFIX)
app.include_router(seller_router.router, prefix=API_PREFIX)
app.include_router(admin_router.router, prefix=API_PREFIX)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "untrade-api"}
