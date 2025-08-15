from pydantic import BaseModel

class OpenAIMessage(BaseModel):
    role: str
    content: str

