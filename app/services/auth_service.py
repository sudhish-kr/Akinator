"""Authentication — bcrypt password hashing + JWT tokens (SDD v1.0)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.db.repositories.user_repository import UserRepository


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: UUID) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise AuthError("Invalid or expired token") from exc


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    async def register(self, email: str, username: str, password: str) -> dict:
        existing = await self.users.get_by_email(email)
        if existing:
            raise AuthError("An account with this email already exists", 409)

        user = await self.users.create(
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        await self.users.commit()
        return {
            "access_token": create_access_token(user.id),
            "token_type": "bearer",
            "user": {"id": str(user.id), "email": user.email, "username": user.username},
        }

    async def login(self, email: str, password: str) -> dict:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")

        return {
            "access_token": create_access_token(user.id),
            "token_type": "bearer",
            "user": {"id": str(user.id), "email": user.email, "username": user.username},
        }
