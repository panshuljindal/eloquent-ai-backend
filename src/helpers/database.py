from __future__ import annotations
import os
from functools import lru_cache

from sqlmodel import SQLModel, Session, create_engine

DB_URL: str = os.getenv("DATABASE_URL", "sqlite:///./chat.db")


@lru_cache
def get_db_engine():
    """Create and cache a synchronous SQLModel engine.

    In dev, ensure tables exist on first access.
    """
    engine = create_engine(DB_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


def get_db_session() -> Session:
    """Return a new Session bound to the cached engine.

    Caller is responsible for closing it (use context manager in controllers).
    """
    engine = get_db_engine()
    return Session(engine)