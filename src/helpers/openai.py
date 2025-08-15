from __future__ import annotations
import os
from functools import lru_cache
from openai import OpenAI

from src.sql_models.message import Message


class OpenAIHelper:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_response(self, messages: list[Message], model: str = "gpt-4o") -> str:
        """Generate an assistant message text from a list of prior messages.

        Returns the textual output produced by the model.
        """
        response = self.client.responses.parse(
            model=model,
            input=[{"role": message.role, "content": message.content} for message in messages],
        )
        return response.output_text


@lru_cache
def get_openai_helper() -> OpenAIHelper:
    return OpenAIHelper()
