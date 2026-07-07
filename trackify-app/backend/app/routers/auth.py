import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..dependencies import get_db, get_redis
from ..models.user import User
from ..schemas.user import AccessTokenResponse, TokenResponse, UserLogin, UserMe, UserRegister
from ..services import auth_service, cache_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _refresh_redis_key(jti: str) -> str:
    return f"refresh:{jti}"


async def _issue_tokens(user: User, response: Response, redis_client: Redis) -> TokenResponse:
    access_token = auth_service.create_access_token(user.id)
    refresh_token, jti = auth_service.create_refresh_token(user.id)

    await cache_service.set_value(
        redis_client,
        _refresh_redis_key(jti),
        str(user.id),
        ttl_seconds=settings.refresh_token_expire_minutes * 60,
    )

    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
        path="/auth",
    )
    return TokenResponse(access_token=access_token, user=UserMe.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> TokenResponse:
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already registered")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=auth_service.hash_password(body.password),
    )
    db.add(user)
    await db.commit()

    return await _issue_tokens(user, response, redis_client)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    invalid_credentials = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user is None or not auth_service.verify_password(body.password, user.hashed_password):
        raise invalid_credentials

    return await _issue_tokens(user, response, redis_client)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    redis_client: Redis = Depends(get_redis),
) -> None:
    if refresh_token:
        try:
            payload = auth_service.decode_token(refresh_token, expected_type="refresh")
            await cache_service.delete_value(redis_client, _refresh_redis_key(payload["jti"]))
        except auth_service.TokenError:
            pass
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth")


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    refresh_token: str | None = Cookie(default=None),
    redis_client: Redis = Depends(get_redis),
) -> AccessTokenResponse:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    if refresh_token is None:
        raise unauthorized

    try:
        payload = auth_service.decode_token(refresh_token, expected_type="refresh")
    except auth_service.TokenError:
        raise unauthorized

    stored_user_id = await cache_service.get_value(redis_client, _refresh_redis_key(payload["jti"]))
    if stored_user_id is None or stored_user_id != payload["sub"]:
        raise unauthorized

    access_token = auth_service.create_access_token(uuid.UUID(payload["sub"]))
    return AccessTokenResponse(access_token=access_token)
