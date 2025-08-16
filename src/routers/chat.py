from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session
from datetime import datetime, UTC

from src.constants.prompts import HUMAN_PROMPT, SYSTEM_PROMPT, SUMMARY_PROMPT
from src.constants.role import Role
from src.controllers.auth import get_user_by_id
from src.controllers.conversation import (
    create_conversation,
    create_message,
    get_conversation_by_id,
    get_conversation_messages,
    get_conversations_by_user_id,
    update_conversation,
)
from src.helpers.database import get_db_session
from src.helpers.filter_message import filter_messages
from src.helpers.openai import OpenAIHelper, get_openai_helper
from src.helpers.pinecone import PineconeHelper, get_pinecone_helper
from src.helpers.response import api_response       
from src.models.chat import ChatRequest
from src.helpers.guardrails import GuardrailsHelper, get_guardrails_helper
from src.sql_models.message import Message

router = APIRouter(prefix="/chat")

@router.post("/create")
def chat(
    request: ChatRequest,
    openai_helper: OpenAIHelper = Depends(get_openai_helper),
    pinecone_helper: PineconeHelper = Depends(get_pinecone_helper),
    guardrails: GuardrailsHelper = Depends(get_guardrails_helper),
    session: Session = Depends(get_db_session),
):
    conversation = get_conversation_by_id(request.conversation_id, session)
    messages = []
    if conversation is None:
        conversation = create_conversation(request.user_id, None, None, session)
        messages = [create_message(conversation.id, Role.SYSTEM, SYSTEM_PROMPT, None, session)]
    else:
        messages = get_conversation_messages(conversation.id, session)
        
    if conversation.is_deleted:
        return api_response({"message": "Conversation is deleted"}, 400)
    
    is_safe_prompt, sanitized_user_text = guardrails.sanitize_user_text(request.message)
    if not is_safe_prompt:
        user_message = create_message(conversation.id, Role.GUARDRAILS, sanitized_user_text, request.message, session)
        messages.append(user_message)
        return api_response({"messages": filter_messages(messages), "conversation_id": conversation.id})

    docs = pinecone_helper.query(sanitized_user_text, top_k=10)
    user_message = create_message(conversation.id, Role.USER, HUMAN_PROMPT.format(USER_QUERY=sanitized_user_text, CONTEXT_SNIPPETS=docs), sanitized_user_text, session)
    messages.append(user_message)

    response_text = openai_helper.generate_response(messages)
    validated = guardrails.validate_output(response_text)

    create_message(conversation.id, Role.ASSISTANT, validated.answer, None, session)
    
    history = get_conversation_messages(conversation.id, session)
    return api_response({"messages": filter_messages(history), "conversation_id": conversation.id})

@router.post("/delete/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    session: Session = Depends(get_db_session),
):
    """Delete a conversation"""
    conversation = get_conversation_by_id(conversation_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)

    conversation.is_deleted = True
    update_conversation(conversation, session)
    return api_response({"message": "Conversation deleted"})

@router.get("/messages/{conversation_id}")
def get_conversation_messages_by_id(
    conversation_id: int,
    session: Session = Depends(get_db_session),
):
    """Get the chat history for a session"""
    conversation = get_conversation_by_id(conversation_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)
    
    history = get_conversation_messages(conversation_id, session)
    return api_response({"messages": filter_messages(history), "conversation_id": conversation_id})

@router.get("/conversations")
def get_user_conversations(
    user_id: int | None = None,
    session: Session = Depends(get_db_session),
):
    """Get conversations for a user by query param"""
    if user_id is None:
        return api_response({"message": "User id is required"}, 400)
    user = get_user_by_id(user_id)
    if user is None:
        return api_response({"message": "User not found"}, 404)
    conversations = get_conversations_by_user_id(user_id, session)
    return api_response({"conversations": conversations})


@router.post("/summarize/{conversation_id}")
def summarize_conversation(
    conversation_id: int,
    openai_helper: OpenAIHelper = Depends(get_openai_helper),
    guardrails: GuardrailsHelper = Depends(get_guardrails_helper),
    session: Session = Depends(get_db_session),
):
    conversation = get_conversation_by_id(conversation_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)

    history = get_conversation_messages(conversation_id, session)
    context_text = "\n\n".join(
        f"{message.role}: {message.user_message if message.role == Role.USER else message.content}" for message in history if message.role != Role.SYSTEM
    )
    
    messages = [Message(conversation_id=conversation_id, role=Role.SYSTEM, content=SUMMARY_PROMPT.format(CONTEXT=context_text), user_message=None, created_at=datetime.now(UTC))]

    raw_summary = openai_helper.generate_response(messages)
    validated = guardrails.validate_output(raw_summary)

    return api_response({"summary": validated.answer})