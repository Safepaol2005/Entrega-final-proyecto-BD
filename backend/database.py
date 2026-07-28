"""Async MySQL connection pool and raw SQL helpers for UnTrade."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Mapping, Optional, Sequence

import aiomysql
from aiomysql.cursors import DictCursor
from fastapi import HTTPException, status

from config import get_settings

# MySQL SIGNAL SQLSTATE '45000' maps to errno 1644
MYSQL_SIGNAL_ERRNO = 1644

_pool: Optional[aiomysql.Pool] = None


class BusinessRuleError(Exception):
    """Raised when a MySQL trigger/procedure signals SQLSTATE 45000."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _extract_mysql_message(exc: BaseException) -> str:
    args = getattr(exc, "args", ())
    if len(args) >= 2 and isinstance(args[1], str):
        return args[1]
    return str(exc)


def is_signal_45000(exc: BaseException) -> bool:
    """Return True if the exception comes from SIGNAL SQLSTATE '45000'."""
    errno = getattr(exc, "args", (None,))[0]
    sqlstate = getattr(exc, "sqlstate", None)
    return errno == MYSQL_SIGNAL_ERRNO or sqlstate == "45000"


async def init_pool() -> aiomysql.Pool:
    """Create the global aiomysql connection pool."""
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    pool_kwargs: dict[str, Any] = {
        "user": settings.db_user,
        "password": settings.db_password,
        "db": settings.db_name,
        "charset": "utf8mb4",
        "autocommit": False,
        "minsize": 1,
        "maxsize": 10,
        "cursorclass": DictCursor,
    }
    if settings.db_unix_socket:
        pool_kwargs["unix_socket"] = settings.db_unix_socket
    else:
        pool_kwargs["host"] = settings.db_host
        pool_kwargs["port"] = settings.db_port

    try:
        _pool = await aiomysql.create_pool(**pool_kwargs)
    except Exception as exc:
        errno = getattr(exc, "args", (None,))[0]
        if errno == 1045:
            raise RuntimeError(
                "MySQL access denied (1045). Set DB_USER/DB_PASSWORD in backend/.env "
                "(root with an empty password is rejected over TCP). "
                f"Tried user={settings.db_user!r} host={settings.db_host!r}."
            ) from exc
        raise
    return _pool


async def close_pool() -> None:
    """Close and clear the global connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


def get_pool() -> aiomysql.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_pool() first.")
    return _pool


@asynccontextmanager
async def acquire_connection() -> AsyncIterator[aiomysql.Connection]:
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def _run_on_connection(
    conn: aiomysql.Connection,
    sql: str,
    params: Optional[Sequence[Any] | Mapping[str, Any]] = None,
    *,
    fetch: Optional[str] = None,
) -> Any:
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        if fetch == "one":
            return await cur.fetchone()
        if fetch == "all":
            return await cur.fetchall()
        return {
            "lastrowid": cur.lastrowid,
            "rowcount": cur.rowcount,
        }


@asynccontextmanager
async def transaction() -> AsyncIterator[aiomysql.Connection]:
    """Acquire a connection and commit/rollback as a single unit of work."""
    async with acquire_connection() as conn:
        try:
            yield conn
            await conn.commit()
        except Exception as exc:
            await conn.rollback()
            if is_signal_45000(exc):
                raise BusinessRuleError(_extract_mysql_message(exc)) from exc
            raise


async def execute(
    sql: str,
    params: Optional[Sequence[Any] | Mapping[str, Any]] = None,
    *,
    fetch: Optional[str] = None,
    commit: bool = True,
    connection: Optional[aiomysql.Connection] = None,
) -> Any:
    """
    Execute a parameterized SQL statement.

    fetch:
      - None: return lastrowid / rowcount dict
      - "one": return a single dict row or None
      - "all": return list of dict rows

    Pass `connection` to participate in an outer `transaction()` block
    (caller owns commit/rollback; `commit` is ignored).
    """
    if connection is not None:
        try:
            return await _run_on_connection(connection, sql, params, fetch=fetch)
        except Exception as exc:
            if is_signal_45000(exc):
                raise BusinessRuleError(_extract_mysql_message(exc)) from exc
            raise

    async with acquire_connection() as conn:
        try:
            result = await _run_on_connection(conn, sql, params, fetch=fetch)
            if commit:
                await conn.commit()
            return result
        except Exception as exc:
            await conn.rollback()
            if is_signal_45000(exc):
                raise BusinessRuleError(_extract_mysql_message(exc)) from exc
            raise


async def call_procedure(
    name: str,
    params: Optional[Sequence[Any]] = None,
) -> list[dict[str, Any]]:
    """
    Execute CALL <procedure>(...) and return any result sets as a list of rows.
    Maps MySQL SIGNAL 45000 to BusinessRuleError.
    """
    placeholders = ", ".join(["%s"] * len(params or ()))
    sql = f"CALL {name}({placeholders})"

    async with acquire_connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute(sql, params or ())
                rows: list[dict[str, Any]] = []
                # Drain all result sets produced by the procedure
                while True:
                    partial = await cur.fetchall()
                    if partial:
                        rows.extend(partial)
                    if not await cur.nextset():
                        break
            await conn.commit()
            return rows
        except Exception as exc:
            await conn.rollback()
            if is_signal_45000(exc):
                raise BusinessRuleError(_extract_mysql_message(exc)) from exc
            raise


def raise_http_from_business_rule(exc: BusinessRuleError) -> None:
    """Map a BusinessRuleError to HTTP 400 (never returns)."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=exc.message,
    ) from exc
