"""SQLAlchemy engine/session setup, per engineering_spec.md's `db/` module.

Reads DATABASE_URL from .env (see docs/database_setup.md, task 63) --
never hardcode credentials here.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")


class Base(DeclarativeBase):
    pass


def get_engine(database_url: str | None = None):
    url = database_url or DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL not set -- copy .env.example to .env and fill it in")
    return create_engine(url)


def get_session_factory(database_url: str | None = None):
    return sessionmaker(bind=get_engine(database_url))
