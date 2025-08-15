import os
from functools import lru_cache
from openai import OpenAI
from pydantic import BaseModel
from typing import Type
from src.sql_models.message import Message
from src.models.message import OpenAIMessage


class OpenAIHelper:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_response(self, messages: list[Message], model: str = "gpt-4o", response_format: Type[BaseModel] = OpenAIMessage) -> BaseModel:
        response = self.client.responses.parse(
            model=model,
            input=[{"role": message.role, "content": message.content} for message in messages],
            text_format=response_format,
        )
        return response.output_parsed


@lru_cache
def get_openai_helper() -> OpenAIHelper:
    return OpenAIHelper()
