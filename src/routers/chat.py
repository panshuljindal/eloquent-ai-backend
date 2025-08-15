from fastapi import APIRouter, Depends
from src.helpers.openai import OpenAIHelper, get_openai_helper
from src.helpers.pinecone import PineconeHelper, get_pinecone_helper
from src.controllers.conversation_controller import create_conversation, get_conversation_by_id, get_conversation_messages, create_message
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
        conversation = create_conversation(None, None, None, session)
        messages = [create_message(conversation.id, Role.SYSTEM, SYSTEM_PROMPT, None, session)]
    else:
        messages = get_conversation_messages(conversation.id, session)
    docs = pinecone_helper.query(request.message, top_k=10)
    user_message = create_message(conversation.id, Role.USER, HUMAN_PROMPT.format(USER_QUERY=request.message, CONTEXT_SNIPPETS=docs), request.message, session)
    messages.append(user_message)

    response = openai_helper.generate_response(messages)
    create_message(conversation.id, Role.ASSISTANT, response.content, None, session)
    
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
    return api_response({"messages": filter_messages(history), "conversation_id": conversation_id})