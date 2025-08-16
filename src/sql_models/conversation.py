from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(index=True, nullable=True)
    short_name: str | None = Field(index=True, nullable=True)
    created_at: datetime = Field()
    is_deleted: bool = Field(default=False)