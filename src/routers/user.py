from fastapi import APIRouter, Depends
from src.controllers.user_controller import add_user, delete_user, get_user_by_id, get_user_by_email, get_conversation
from src.helpers.database import get_db_session
from sqlmodel import Session
from src.helpers.response import api_response
from src.sql_models.user import User

router = APIRouter(prefix="/user")

@router.post("/create")
def create_user_route(user: User):
    """Create a new user"""
    if get_user_by_email(user.email) is not None:
        return api_response({"message": "User already exists"}, 400)
    user = add_user(user.email, user.name, user.password)
    return api_response({"message": "User created", "user": user}, 201)

@router.delete("/delete/{user_id}")
def delete_user_route(user_id: int):
    """Delete a user"""
    if delete_user(user_id):
        return api_response({"message": "User deleted"}, 200)
    return api_response({"message": "User not found"}, 404)

@router.get("/conversations/{user_id}")
def get_conversations_by_user_id(
    user_id: int | None,
    session: Session = Depends(get_db_session),
):
    """Get a conversation by its user id"""
    if user_id is None:
        return api_response({"message": "User id is required"}, 400)
    user = get_user_by_id(user_id, session)
    if user is None:
        return api_response({"message": "User not found"}, 404)
    conversation = get_conversation(user_id, session)
    if conversation is None:
        return api_response({"message": "Conversation not found"}, 404)
    return api_response({"messages": [], "conversation_id": conversation.id})