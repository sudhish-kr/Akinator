from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RefreshToken, RevokedAccessToken, User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash)
        self.db.add(user)
        await self.db.flush()
        return user

    async def store_refresh_token(
        self,
        user_id: UUID,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        record = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_refresh_token(self, jti: str) -> RefreshToken | None:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, jti: str) -> bool:
        record = await self.get_refresh_token(jti)
        if not record or record.revoked_at is not None:
            return False
        record.revoked_at = datetime.now(timezone.utc)
        return True

    async def revoke_all_refresh_tokens(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        rows = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for row in rows:
            row.revoked_at = now
        return len(rows)

    async def revoke_access_token(self, jti: str, expires_at: datetime) -> None:
        existing = await self.db.get(RevokedAccessToken, jti)
        if existing:
            return
        self.db.add(RevokedAccessToken(jti=jti, expires_at=expires_at))
        await self.db.flush()

    async def is_access_token_revoked(self, jti: str) -> bool:
        return (await self.db.get(RevokedAccessToken, jti)) is not None

    async def commit(self) -> None:
        await self.db.commit()
