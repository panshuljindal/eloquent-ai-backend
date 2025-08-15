from sqlmodel import Field, SQLModel
from datetime import datetime

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    password: str = Field(index=True)
    created_at: datetime = Field(default=None)