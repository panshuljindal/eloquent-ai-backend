from __future__ import annotations
import os
from functools import lru_cache
from openai import OpenAI

from src.sql_models.message import Message
from src.constants.role import Role

class OpenAIHelper:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_response(self, messages: list[Message], model: str = "gpt-4o") -> str:
        """Generate an assistant message text from a list of prior messages.

        Returns the textual output produced by the model.
        """

        response = self.client.responses.parse(
            model=model,
            input=[{"role": message.role if message.role != Role.GUARDRAILS else Role.USER, "content": message.content} for message in messages],
        )
        return response.output_text

    def stream_response(self, messages: list[Message], model: str = "gpt-4o"):
        """Stream assistant output tokens as they are produced by the model.

        Yields small text deltas (strings). Caller is responsible for assembling
        the final text if needed.
        """
        with self.client.responses.stream(
            model=model,
            input=[{"role": message.role if message.role != Role.GUARDRAILS else Role.USER, "content": message.content} for message in messages],
        ) as stream:
            for event in stream:
                if getattr(event, "type", "") == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield delta
                elif getattr(event, "type", "") == "response.error":
                    err = getattr(event, "error", None)
                    message = getattr(err, "message", None) if err is not None else None
                    raise RuntimeError(message or "Model streaming error")
            _ = stream.get_final_response()

@lru_cache
def get_openai_helper() -> OpenAIHelper:
    return OpenAIHelper()
