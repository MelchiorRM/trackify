import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .database import SessionLocal
from .models.user import User
from .redis import redis_client
from .services.auth_service import TokenError, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_redis() -> Redis:
    return redis_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except TokenError:
        raise unauthorized

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise unauthorized
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like get_current_user, but returns None instead of 401ing — for
    endpoints that serve both logged-out and logged-in viewers (e.g. GET
    /likes on a public post/review), where visibility still needs to be
    checked against whoever (if anyone) is asking."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except TokenError:
        return None
    return await db.get(User, uuid.UUID(payload["sub"]))
