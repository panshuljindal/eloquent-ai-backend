from pydantic import BaseModel
from src.sql_models.message import Message

class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str

class ChatResponse(BaseModel):
    messages: list[Message] | None = None