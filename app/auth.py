from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AuthSession, Role, User

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("not-a-real-user-password")
bearer = HTTPBearer(auto_error=False)
_attempts: dict[str, deque[datetime]] = defaultdict(deque)
_attempt_lock = Lock()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def check_login_rate(request: Request) -> None:
    address = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    with _attempt_lock:
        attempts = _attempts[address]
        while attempts and attempts[0] < now - timedelta(minutes=1):
            attempts.popleft()
        if len(attempts) >= 10:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts")
        attempts.append(now)


def issue_token(db: Session, user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.jwt_expiry_minutes)
    token_id = str(uuid4())
    db.add(AuthSession(id=token_id, user_id=user.id, expires_at=expires))
    db.commit()
    return jwt.encode(
        {"sub": str(user.id), "role": user.role.value, "jti": token_id, "iat": now, "exp": expires},
        settings.jwt_secret,
        algorithm="HS256",
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "A valid bearer token is required")
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=["HS256"])
        user_id, token_id = int(payload["sub"]), str(payload["jti"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise unauthorized from None
    active = db.scalar(
        select(AuthSession.id)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.id == token_id,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(timezone.utc),
            User.is_active.is_(True),
        )
    )
    if active is None:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


def revoke_token(db: Session, raw_token: str) -> None:
    try:
        payload = jwt.decode(raw_token, get_settings().jwt_secret, algorithms=["HS256"])
        token_id = str(payload["jti"])
    except (jwt.PyJWTError, KeyError, TypeError):
        return
    session = db.get(AuthSession, token_id)
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


def require_roles(*roles: Role):
    def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return dependency
