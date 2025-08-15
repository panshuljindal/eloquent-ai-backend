from sqlmodel import Field, SQLModel
from datetime import datetime, UTC

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True)
    role: str = Field(index=True)
    content: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now(UTC))

    