from __future__ import annotations

from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: int | None = None
    conversation_id: int | None = None
    message: str

class UserMessage(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    messages: list[UserMessage] | None = None