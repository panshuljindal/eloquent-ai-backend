from src.sql_models.conversation import Conversation
from src.sql_models.message import Message
from datetime import datetime, UTC
from sqlmodel import select, Session

def get_conversation_by_id(conversation_id: int | None, session: Session) -> Conversation | None:
    """Get a conversation by its id"""
    if conversation_id is None:
        return None
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        return None
    return conversation

def get_conversation_messages(conversation_id: int, session: Session) -> list[Message]:
    """Get the chat history for a conversation"""
    query = select(Message).where(Message.conversation_id == conversation_id)
    return list(session.exec(query))

def create_conversation(user_id: int | None, short_name: str | None, description: str | None, session: Session) -> Conversation:
    """Create a new conversation"""
    conversation = Conversation(user_id=user_id, created_at=datetime.now(UTC))
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation

def create_message(conversation_id: int, role: str, content: str, user_message: str | None, session: Session) -> Message:
    """Create a new message"""
    message = Message(conversation_id=conversation_id, role=role, content=content, user_message=user_message, created_at=datetime.now(UTC))
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_conversations_by_user_id(user_id: int, session: Session) -> list[Conversation]:
    """Get a conversation by its user id"""
    query = select(Conversation).where(Conversation.user_id == user_id)
    return session.exec(query).all()
