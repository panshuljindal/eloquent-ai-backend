from fastapi import APIRouter, Depends
from src.helpers.openai import OpenAIHelper, get_openai_helper
from src.helpers.pinecone import PineconeHelper, get_pinecone_helper
from src.controllers.conversation import create_conversation, get_conversation_by_id, get_conversation_messages, create_message, get_conversations_by_user_id
from src.controllers.auth import get_user_by_id
from src.models.chat import ChatRequest
from src.helpers.database import get_db_session
from sqlmodel import Session
from src.helpers.response import api_response
from src.constants.role import Role
from src.constants.prompts import SYSTEM_PROMPT, HUMAN_PROMPT
from src.helpers.filter_message import filter_messages

router = APIRouter(prefix="/chat")

@router.post("/create")
def chat(
    request: ChatRequest,
    openai_helper: OpenAIHelper = Depends(get_openai_helper),
    pinecone_helper: PineconeHelper = Depends(get_pinecone_helper),
    session: Session = Depends(get_db_session),
):
    conversation = get_conversation_by_id(request.conversation_id, session)
    messages = []
    if conversation is None:
        conversation = create_conversation(request.user_id, None, None, session)
        messages = [create_message(conversation.id, Role.SYSTEM, SYSTEM_PROMPT, None, session)]
    else:
        messages = get_conversation_messages(conversation.id, session)
    docs = pinecone_helper.query(request.message, top_k=10)
    user_message = create_message(conversation.id, Role.USER, HUMAN_PROMPT.format(USER_QUERY=request.message, CONTEXT_SNIPPETS=docs), request.message, session)
    messages.append(user_message)

    response = openai_helper.generate_response(messages)
    create_message(conversation.id, Role.ASSISTANT, response, None, session)
    
    history = get_conversation_messages(conversation.id, session)
    return api_response({"messages": filter_messages(history), "conversation_id": conversation.id})

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
    print(history)
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