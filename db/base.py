"""SQLAlchemy engine/session setup, per engineering_spec.md's `db/` module.

Reads DATABASE_URL from .env (see docs/database_setup.md, task 63) --
never hardcode credentials here.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def normalize_database_url(url: str | None) -> str | None:
    """Managed Postgres providers (Supabase, Neon, Render) hand out
    `postgres://` / `postgresql://` URLs; SQLAlchemy 2.1 maps those to
    psycopg3, which isn't installed. Pin the psycopg2 driver instead."""
    if not url:
        return url
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


DATABASE_URL = normalize_database_url(os.environ.get("DATABASE_URL"))


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=8)
def _cached_engine(url: str):
    # pool_pre_ping + pool_recycle: managed poolers (Supabase, Neon) drop idle
    # connections; without these the first query after a quiet spell fails.
    return create_engine(url, pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=5)


def get_engine(database_url: str | None = None):
    """One engine (and connection pool) per URL for the process lifetime --
    creating one per request would open a new TLS connection each time and
    exhaust a hosted pooler's connection limit."""
    url = normalize_database_url(database_url) or DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL not set -- copy .env.example to .env and fill it in")
    return _cached_engine(url)


@lru_cache(maxsize=8)
def _cached_session_factory(engine):
    return sessionmaker(bind=engine)


def get_session_factory(database_url: str | None = None):
    return _cached_session_factory(get_engine(database_url))
