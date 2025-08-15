from sqlmodel import Field, SQLModel
from datetime import datetime

class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(index=True, nullable=True)
    created_at: datetime = Field()