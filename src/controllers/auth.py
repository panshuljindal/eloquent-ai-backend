from __future__ import annotations

from datetime import UTC, datetime

import bcrypt
from sqlmodel import select
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.helpers.database import get_db_session
from src.sql_models.user import User
from src.helpers.jwt import create_access_token, decode_token

bearer_scheme = HTTPBearer(auto_error=False)

def add_user(email: str, name: str, password: str) -> User:
    with get_db_session() as session:
        user = User(
            email=email,
            name=name,
            password=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            created_at=datetime.now(UTC),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def delete_user(user_id: int) -> bool:
    with get_db_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return False
        session.delete(user)
        session.commit()
        return True

def get_user_by_id(user_id: int | None) -> User | None:
    if user_id is None:
        return None
    with get_db_session() as session:
        return session.get(User, user_id)

def get_user_by_email(email: str | None) -> User | None:
    if email is None:
        return None
    with get_db_session() as session:
        return session.exec(select(User).where(User.email == email)).first()

def create_user_token(user: User) -> str:
    return create_access_token({"user_id": str(user.id), "email": user.email})

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> User:
    """Get the current user from the token, if the token is not provided, raise an error"""
    if credentials is None or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = get_user_by_id(int(user_id_str))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def get_current_user_optional(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> User | None:
    """Get the current user from the token, if the token is not provided, return None"""
    if credentials is None or not credentials.scheme or credentials.credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None:
        return None
    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = get_user_by_id(int(user_id_str))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
