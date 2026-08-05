from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories.game_repository import GameRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_db
from app.services.auth_service import AuthError, AuthService, decode_access_token
from app.services.game_service import GameService


async def get_game_repository(db: AsyncSession = Depends(get_db)) -> GameRepository:
    return GameRepository(db)


async def get_game_service(db: AsyncSession = Depends(get_db)) -> GameService:
    return GameService(GameRepository(db))


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


async def get_optional_user_id(
    authorization: str | None = Header(default=None),
) -> UUID | None:
    """Guest play is allowed (TDD Section 5.5) — token is optional."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        return decode_access_token(token)
    except AuthError:
        return None


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        user_id = decode_access_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
