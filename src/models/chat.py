from pydantic import BaseModel
from src.sql_models.message import Message

class ChatRequest(BaseModel):
    user_id: int | None = None
    conversation_id: int | None = None
    message: str

class UserMessage(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    messages: list[UserMessage] | None = None