from sqlmodel import Field, SQLModel
from datetime import datetime, UTC

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    password: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now(UTC))