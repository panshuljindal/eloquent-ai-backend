from __future__ import annotations

from src.constants.role import Role
from src.models.chat import UserMessage
from src.sql_models.message import Message

def filter_messages(messages: list[Message]) -> list[UserMessage]:
    final_messages = []
    for message in messages:
        if message.role == Role.SYSTEM:
            continue
        elif message.role == Role.USER:
            final_messages.append(UserMessage(role=message.role, content=message.user_message))
        elif message.role == Role.GUARDRAILS:
            final_messages.append(UserMessage(role=Role.USER, content=message.user_message))
            final_messages.append(UserMessage(role=Role.ASSISTANT, content=message.content))
        else:
            final_messages.append(UserMessage(role=message.role, content=message.content))
    return final_messages