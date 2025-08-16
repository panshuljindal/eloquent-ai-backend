from __future__ import annotations
import os
from functools import lru_cache

from sqlmodel import SQLModel, Session, create_engine
from typing import Iterator

DB_URL: str = os.getenv("DATABASE_URL", "sqlite:///./chat.db")


@lru_cache
def get_db_engine():
    """Create and cache a synchronous SQLModel engine.

    In dev, ensure tables exist on first access. Adds sane pool defaults
    and enables pre-ping to avoid stale connections.
    """
    pool_size = int(os.getenv("DB_POOL_SIZE", "30"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))

    engine = create_engine(
        DB_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def get_db_session() -> Session:
    """Return a new Session bound to the cached engine.

    Caller is responsible for closing it (use context manager in controllers).
    """
    engine = get_db_engine()
    return Session(engine)


def get_db_session_dep() -> Iterator[Session]:
    """FastAPI dependency that yields a Session and ensures it is closed.

    Use as: Depends(get_db_session_dep)
    """
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()