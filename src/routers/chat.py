from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
import json
from sqlmodel import Session
from datetime import datetime, UTC

from src.constants.prompts import HUMAN_PROMPT, SYSTEM_PROMPT, SUMMARY_PROMPT
from src.constants.role import Role
from src.controllers.auth import get_current_user, get_current_user_optional, get_user_by_id
from src.helpers.jwt import decode_token
from src.controllers.conversation import (
    create_conversation,
    create_message,
    get_conversation_by_id,
    get_conversation_messages,
    get_conversations_by_user_id,
    update_conversation,
)
from src.helpers.database import get_db_session_dep
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
    session: Session = Depends(get_db_session_dep),
    current_user = Depends(get_current_user_optional),
):
    conversation = get_conversation_by_id(request.conversation_id, session)
    if conversation is None:
        user_id = current_user.id if current_user is not None else None
        conversation = create_conversation(user_id, session)
        messages: list[Message] = [create_message(conversation.id, Role.SYSTEM, SYSTEM_PROMPT, None, session)]
    else:
        if conversation.user_id is not None:
            if current_user is None or conversation.user_id != current_user.id:
                return api_response({"message": "Forbidden"}, 403)
        messages: list[Message] = get_conversation_messages(conversation.id, session)
        
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
    create_message(conversation.id, Role.ASSISTANT, response_text, None, session)
    
    history = get_conversation_messages(conversation.id, session)
    return api_response({"messages": filter_messages(history), "conversation_id": conversation.id})

@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    openai_helper: OpenAIHelper = Depends(get_openai_helper),
    pinecone_helper: PineconeHelper = Depends(get_pinecone_helper),
    guardrails: GuardrailsHelper = Depends(get_guardrails_helper),
    session: Session = Depends(get_db_session_dep),
    current_user = Depends(get_current_user_optional),
):
    """Stream the assistant response over HTTP as server-sent events (SSE)."""
    conversation = get_conversation_by_id(request.conversation_id, session)
    if conversation is None:
        user_id = current_user.id if current_user is not None else None
        conversation = create_conversation(user_id, session)
        messages: list[Message] = [create_message(conversation.id, Role.SYSTEM, SYSTEM_PROMPT, None, session)]
    else:
        if conversation.user_id is not None:
            if current_user is None or conversation.user_id != current_user.id:
                return api_response({"message": "Forbidden"}, 403)
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

    def sse_generator():
        buffer = ""
        try:
            for delta in openai_helper.stream_response(messages):
                buffer += delta
                yield f"data: {json.dumps({'delta': delta})}\n\n"
        except Exception as e:
            if buffer.strip():
                create_message(conversation.id, Role.ASSISTANT, buffer, None, session)
            yield f"event: error\n" f"data: {json.dumps({'message': str(e)})}\n\n"
            return
        create_message(conversation.id, Role.ASSISTANT, buffer, None, session)
        history_local = get_conversation_messages(conversation.id, session)
        payload = {"conversation_id": conversation.id, "messages": filter_messages(history_local)}
        yield f"event: done\n" f"data: {json.dumps(jsonable_encoder(payload))}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@router.websocket("/ws/{conversation_id}")
async def chat_websocket(
    websocket: WebSocket,
    conversation_id: int,
    openai_helper: OpenAIHelper = Depends(get_openai_helper),
    pinecone_helper: PineconeHelper = Depends(get_pinecone_helper),
    guardrails: GuardrailsHelper = Depends(get_guardrails_helper),
    session: Session = Depends(get_db_session_dep),
):
    """WebSocket endpoint that streams assistant tokens to the client.
    """
    await websocket.accept()
    try:
        auth_header = websocket.headers.get("authorization")
        token_qs = websocket.query_params.get("token")
        token = None
        if isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
        elif token_qs:
            token = token_qs
        current_user = None
        if token:
            payload = decode_token(token)
            if payload and payload.get("user_id"):
                current_user = get_user_by_id(int(payload["user_id"]))

        data = await websocket.receive_json()
        user_text = data.get("message", "")
        if not isinstance(user_text, str) or not user_text.strip():
            await websocket.send_json({"event": "error", "message": "Missing 'message'"})
            await websocket.close()
            return

        conversation = get_conversation_by_id(conversation_id, session)
        if conversation is None:
            user_id = current_user.id if current_user is not None else None
            conversation = create_conversation(user_id, session)
            messages: list[Message] = [create_message(conversation.id, Role.SYSTEM, SYSTEM_PROMPT, None, session)]
        else:
            if conversation.user_id is not None:
                if current_user is None or conversation.user_id != current_user.id:
                    await websocket.send_json({"event": "error", "message": "Forbidden"})
                    await websocket.close()
                    return
            messages = get_conversation_messages(conversation.id, session)

        if conversation.is_deleted:
            await websocket.send_json({"event": "error", "message": "Conversation is deleted"})
            await websocket.close()
            return

        is_safe_prompt, sanitized_user_text = guardrails.sanitize_user_text(user_text)
        if not is_safe_prompt:
            user_message = create_message(conversation.id, Role.GUARDRAILS, sanitized_user_text, user_text, session)
            messages.append(user_message)
            await websocket.send_json({"event": "guardrails", "messages": filter_messages(messages), "conversation_id": conversation.id})
            await websocket.close()
            return

        docs = pinecone_helper.query(sanitized_user_text, top_k=10)
        user_message = create_message(conversation.id, Role.USER, HUMAN_PROMPT.format(USER_QUERY=sanitized_user_text, CONTEXT_SNIPPETS=docs), sanitized_user_text, session)
        messages.append(user_message)

        buffer = ""
        try:
            for delta in openai_helper.stream_response(messages):
                buffer += delta
                await websocket.send_text(delta)
        except WebSocketDisconnect:
            if buffer.strip():
                create_message(conversation.id, Role.ASSISTANT, buffer, None, session)
            return
        except Exception as e:
            if buffer.strip():
                create_message(conversation.id, Role.ASSISTANT, buffer, None, session)
            await websocket.send_json({"event": "error", "message": str(e)})
            await websocket.close()
            return

        create_message(conversation.id, Role.ASSISTANT, buffer, None, session)
        history = get_conversation_messages(conversation.id, session)
        await websocket.send_json(jsonable_encoder({"event": "done", "conversation_id": conversation.id, "messages": filter_messages(history)}))
        await websocket.close()
    except WebSocketDisconnect:
        return

@router.post("/delete/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    session: Session = Depends(get_db_session_dep),
    current_user = Depends(get_current_user_optional),
):
    """Delete a conversation"""
    conversation = get_conversation_by_id(conversation_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)
    if current_user is not None and conversation.user_id != current_user.id:
        return api_response({"message": "Forbidden"}, 403)
    if conversation.is_deleted:
        return api_response({"message": "Conversation already deleted"}, 400)
    
    conversation.is_deleted = True
    update_conversation(conversation, session)
    return api_response({"message": "Conversation deleted"})

@router.get("/messages/{conversation_id}")
def get_conversation_messages_by_id(
    conversation_id: int,
    session: Session = Depends(get_db_session_dep),
    current_user = Depends(get_current_user_optional),
):
    """Get the chat history for a session"""
    conversation = get_conversation_by_id(conversation_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)
    if current_user is not None and conversation.user_id != current_user.id:
        return api_response({"message": "Forbidden"}, 403)
    if conversation.is_deleted:
        return api_response({"message": "Conversation already deleted"}, 400)

    history = get_conversation_messages(conversation_id, session)
    return api_response({"messages": filter_messages(history), "conversation_id": conversation_id})

@router.get("/conversations")
def get_user_conversations(
    session: Session = Depends(get_db_session_dep),
    current_user = Depends(get_current_user),
):
    """Get conversations for the authenticated user"""
    conversations = get_conversations_by_user_id(current_user.id, session, is_deleted=False)
    return api_response({"conversations": conversations})


@router.post("/summarize/{conversation_id}")
def summarize_conversation(
    conversation_id: int,
    openai_helper: OpenAIHelper = Depends(get_openai_helper),
    session: Session = Depends(get_db_session_dep),
    current_user = Depends(get_current_user_optional),
):
    conversation = get_conversation_by_id(conversation_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)
    if current_user is not None and conversation.user_id != current_user.id:
        return api_response({"message": "Forbidden"}, 403)

    history = get_conversation_messages(conversation_id, session)
    context_text = "\n\n".join(
        f"{message.role}: {message.user_message if message.role == Role.USER else message.content}" for message in history if message.role != Role.SYSTEM
    )
    
    messages = [Message(conversation_id=conversation_id, role=Role.SYSTEM, content=SUMMARY_PROMPT.format(CONTEXT=context_text), user_message=None, created_at=datetime.now(UTC))]
    summary = openai_helper.generate_response(messages)

    return api_response({"summary": summary})