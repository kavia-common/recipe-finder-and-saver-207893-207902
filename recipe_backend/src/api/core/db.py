from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from src.api.core.config import get_settings


@contextmanager
def _get_conn() -> Iterator[psycopg.Connection]:
    """Context manager for DB connections."""
    settings = get_settings()
    conn = psycopg.connect(settings.postgres_url, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


# PUBLIC_INTERFACE
def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    """Fetch a single row from PostgreSQL as a dict."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row is not None else None


# PUBLIC_INTERFACE
def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Fetch all rows from PostgreSQL as a list of dicts."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


# PUBLIC_INTERFACE
def execute(query: str, params: tuple[Any, ...] = ()) -> int:
    """Execute a write query (INSERT/UPDATE/DELETE). Returns affected rowcount."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount
