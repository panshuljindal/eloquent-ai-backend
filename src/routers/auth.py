from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Depends

from src.controllers.auth import add_user, get_user_by_email, create_user_token, get_current_user
from src.helpers.response import api_response
from src.models.auth import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup_route(payload: RegisterRequest):
    """Create a new user"""
    if get_user_by_email(payload.email) is not None:
        return api_response({"message": "User already exists"}, 400)
    db_user = add_user(payload.email, payload.name, payload.password)
    try:
        sanitized = db_user.model_dump(exclude={"password"})
    except Exception:
        sanitized = {"id": db_user.id, "email": db_user.email, "name": db_user.name, "created_at": db_user.created_at}
    token = create_user_token(db_user)
    return api_response({"message": "User created", "user": sanitized, "access_token": token, "token_type": "bearer"}, 201)

@router.post("/login")
def login_route(payload: LoginRequest):
    """Login a user"""
    db_user = get_user_by_email(payload.email)
    if db_user is None:
        return api_response({"message": "User not found"}, 404)
    if not bcrypt.checkpw(payload.password.encode("utf-8"), db_user.password.encode("utf-8")):
        return api_response({"message": "Invalid password"}, 401)
    try:
        sanitized = db_user.model_dump(exclude={"password"})
    except Exception:
        sanitized = {"id": db_user.id, "email": db_user.email, "name": db_user.name, "created_at": db_user.created_at}
    token = create_user_token(db_user)
    return api_response({"message": "User logged in", "user": sanitized, "access_token": token, "token_type": "bearer"}, 200)


@router.get("/me")
def me_route(current_user = Depends(get_current_user)):
    try:
        sanitized = current_user.model_dump(exclude={"password"})
    except Exception:
        sanitized = {"id": current_user.id, "email": current_user.email, "name": current_user.name, "created_at": current_user.created_at}
    return api_response({"user": sanitized})