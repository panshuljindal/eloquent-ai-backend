from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True)
    role: str = Field(index=True)
    content: str = Field(index=True)
    user_message: str | None = Field(index=True, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now(UTC))
