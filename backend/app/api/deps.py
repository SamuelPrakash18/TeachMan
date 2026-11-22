import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers=_UNAUTHORIZED_HEADERS,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise _unauthorized("Invalid or expired token")

    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise _unauthorized("Invalid or expired token")
    return user


def require_tutor(user: User = Depends(get_current_user)) -> User:
    if user.role != "tutor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tutor access required")
    return user


def require_parent(user: User = Depends(get_current_user)) -> User:
    if user.role != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parent access required")
    return user
