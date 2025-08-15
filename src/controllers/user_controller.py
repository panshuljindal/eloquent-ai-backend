import bcrypt
from src.helpers.database import get_db_session
from src.sql_models.user import User
from src.sql_models.conversation import Conversation
from sqlmodel import select, Session

def add_user(email: str, name: str, password: str) -> User:
    with get_db_session() as session:
        user = User(email=email, name=name, password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
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

def get_user_conversations(user_id: int | None, session: Session) -> list[Conversation]:
    """Get a conversation by its user id"""
    query = select(Conversation).where(Conversation.user_id == user_id)
    return session.exec(query).all()
