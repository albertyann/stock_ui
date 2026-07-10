from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    create_refresh_token,
    decode_token,
    generate_invitation_code,
    generate_totp_secret,
    hash_token,
    verify_totp,
)
from app.config import get_settings
from app.models import RefreshToken, User
from fastapi import HTTPException

settings = get_settings()


def _invitation_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        hours=settings.invitation_expire_hours
    )


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def list_users(self) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def create_user(self, phone: str, role: str = "user") -> User:
        if role not in ("admin", "user"):
            raise ValueError(f"Invalid role: {role}")
        if await self.get_by_phone(phone):
            raise ValueError(f"Phone already exists: {phone}")
        user = User(
            phone=phone,
            role=role,
            totp_secret=None,
            invitation_code=generate_invitation_code() if role == "user" else None,
            invitation_expires_at=_invitation_expiry() if role == "user" else None,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_active(self, user_id: int, is_active: bool) -> User:
        user = await self._require_user(user_id)
        user.is_active = is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_totp(self, user_id: int) -> User:
        """清空 TOTP 并重新生成邀请码，用户需要重新走绑定流程。"""
        user = await self._require_user(user_id)
        user.totp_secret = None
        user.enrolled_at = None
        user.invitation_code = generate_invitation_code()
        user.invitation_expires_at = _invitation_expiry()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def begin_enrollment(self, phone: str, invitation_code: str) -> User:
        result = await self.db.execute(
            select(User).where(
                User.phone == phone,
                User.invitation_code == invitation_code,
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("手机号或邀请码无效")
        if user.invitation_expires_at and user.invitation_expires_at < datetime.now(
            timezone.utc
        ):
            raise ValueError("邀请码已过期，请联系管理员重置")
        if user.totp_secret:
            raise ValueError("TOTP 已绑定，请联系管理员重置后再试")
        user.totp_secret = generate_totp_secret()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirm_enrollment(self, user: User, totp_code: str) -> User:
        if not user.totp_secret:
            raise ValueError("TOTP 未生成，请重新发起绑定")
        if not verify_totp(user.totp_secret, totp_code):
            raise ValueError("动态码错误")
        user.enrolled_at = datetime.now(timezone.utc)
        user.invitation_code = None
        user.invitation_expires_at = None
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, phone: str, totp_code: str) -> User:
        user = await self.get_by_phone(phone)
        if not user or not user.is_active or not user.totp_secret:
            raise ValueError("手机号或动态码无效")
        if not verify_totp(user.totp_secret, totp_code):
            raise ValueError("手机号或动态码无效")
        if not user.enrolled_at:
            user.enrolled_at = datetime.now(timezone.utc)
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def issue_refresh_token(self, user_id: int) -> tuple[str, datetime]:
        raw = create_refresh_token(user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        rt = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw),
            expires_at=expires_at,
        )
        self.db.add(rt)
        await self.db.commit()
        return raw, expires_at

    async def verify_refresh_token(self, raw: str) -> User | None:
        try:
            payload = decode_token(raw)
        except HTTPException:
            return None
        if payload.get("type") != "refresh":
            return None
        user_id = int(payload["sub"])
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(raw),
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        rt = result.scalar_one_or_none()
        if not rt:
            return None
        user = await self.get_by_id(user_id)
        return user if (user and user.is_active) else None

    async def revoke_refresh_token(self, raw: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))
        )
        rt = result.scalar_one_or_none()
        if rt and not rt.revoked_at:
            rt.revoked_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def revoke_all_user_tokens(self, user_id: int) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        for rt in result.scalars().all():
            rt.revoked_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def _require_user(self, user_id: int) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        return user
