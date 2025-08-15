import os
from functools import lru_cache
from sqlmodel import create_engine, SQLModel, Session

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")

@lru_cache
def get_db_engine():
    engine = create_engine(DB_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

def get_db_session():
    engine = get_db_engine()
    return Session(engine)