"""JWT authentication — bcrypt passwords, access/refresh tokens, RBAC roles."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.db.models import User
from app.db.repositories.user_repository import UserRepository


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def role_for_user(user: User) -> str:
    return "admin" if user.is_admin else "user"


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user: User) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    jti = uuid4().hex
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    token = _encode(
        {
            "sub": str(user.id),
            "type": "access",
            "role": role_for_user(user),
            "jti": jti,
            "exp": expires,
        }
    )
    return token, jti, expires


def create_refresh_token(user: User) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    jti = uuid4().hex
    expires = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    token = _encode(
        {
            "sub": str(user.id),
            "type": "refresh",
            "role": role_for_user(user),
            "jti": jti,
            "exp": expires,
        }
    )
    return token, jti, expires


def decode_token(token: str, *, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise AuthError("Invalid or expired token") from exc

    if expected_type and payload.get("type") != expected_type:
        raise AuthError("Invalid token type")
    if "sub" not in payload or "jti" not in payload:
        raise AuthError("Invalid token payload")
    return payload


def decode_access_token(token: str) -> UUID:
    """Backward-compatible helper — returns user id from an access token."""
    payload = decode_token(token, expected_type="access")
    try:
        return UUID(payload["sub"])
    except ValueError as exc:
        raise AuthError("Invalid token subject") from exc


def _user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": role_for_user(user),
    }


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    async def _issue_token_pair(self, user: User) -> dict:
        access, _, _ = create_access_token(user)
        refresh, refresh_jti, refresh_exp = create_refresh_token(user)
        await self.users.store_refresh_token(user.id, refresh_jti, refresh_exp)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": _user_payload(user),
        }

    async def register(self, email: str, username: str, password: str) -> dict:
        existing = await self.users.get_by_email(email)
        if existing:
            raise AuthError("An account with this email already exists", 409)

        user = await self.users.create(
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        tokens = await self._issue_token_pair(user)
        await self.users.commit()
        return tokens

    async def login(self, email: str, password: str) -> dict:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")

        tokens = await self._issue_token_pair(user)
        await self.users.commit()
        return tokens

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload["jti"]
        record = await self.users.get_refresh_token(jti)
        if not record or record.revoked_at is not None:
            raise AuthError("Refresh token revoked or unknown")

        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AuthError("Refresh token expired")

        user = await self.users.get_by_id(UUID(payload["sub"]))
        if not user:
            raise AuthError("User no longer exists")

        # Rotate: revoke old refresh, issue a new pair
        await self.users.revoke_refresh_token(jti)
        tokens = await self._issue_token_pair(user)
        await self.users.commit()
        return tokens

    async def logout(
        self,
        refresh_token: str | None = None,
        access_token: str | None = None,
    ) -> dict:
        revoked = 0

        if refresh_token:
            try:
                payload = decode_token(refresh_token, expected_type="refresh")
                if await self.users.revoke_refresh_token(payload["jti"]):
                    revoked += 1
            except AuthError:
                pass

        if access_token:
            try:
                payload = decode_token(access_token, expected_type="access")
                exp = payload.get("exp")
                if isinstance(exp, (int, float)):
                    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                else:
                    expires_at = datetime.now(timezone.utc) + timedelta(
                        minutes=settings.jwt_expire_minutes
                    )
                await self.users.revoke_access_token(payload["jti"], expires_at)
                revoked += 1
            except AuthError:
                pass

        await self.users.commit()
        return {"status": "logged_out", "revoked": revoked}

    async def assert_access_token_valid(self, token: str) -> User:
        payload = decode_token(token, expected_type="access")
        if await self.users.is_access_token_revoked(payload["jti"]):
            raise AuthError("Token has been revoked")
        user = await self.users.get_by_id(UUID(payload["sub"]))
        if not user:
            raise AuthError("User no longer exists")
        return user
