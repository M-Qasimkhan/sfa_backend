from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import Role, Session as SessionModel, User
from app.config import settings


def get_current_user(request: Request, db: DbSession = Depends(get_db)) -> User:
    session_key = request.cookies.get(settings.COOKIE_NAME)
    if not session_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_key == session_key)
        .first()
    )

    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active")

    return user


def require_roles(*allowed_roles: Role):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.COOKIE_NAME, httponly=True, samesite="lax")
