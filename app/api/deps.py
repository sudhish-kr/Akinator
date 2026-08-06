from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories.game_repository import GameRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_db
from app.services.auth_service import AuthError, AuthService
from app.services.game_service import GameService


async def get_game_repository(db: AsyncSession = Depends(get_db)) -> GameRepository:
    return GameRepository(db)


async def get_game_service(db: AsyncSession = Depends(get_db)) -> GameService:
    return GameService(GameRepository(db))


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1]


async def get_optional_user_id(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> UUID | None:
    """Guest play is allowed — token is optional."""
    token = _bearer_token(authorization)
    if not token:
        return None
    try:
        user = await AuthService(UserRepository(db)).assert_access_token_valid(token)
        return user.id
    except AuthError:
        return None


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = _bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return await AuthService(UserRepository(db)).assert_access_token_valid(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


async def require_user(user: User = Depends(get_current_user)) -> User:
    """Any authenticated user (role user or admin)."""
    return user
