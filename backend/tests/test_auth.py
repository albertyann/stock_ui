"""Auth 模块测试。

测试分两类：
  - 纯函数测试（test_*_pure）：永远可跑，不依赖 DB
  - DB 集成测试（TestUserServiceDB / TestAuthRouterIntegration）：依赖本地 PostgreSQL，
    测试前会清理本测试使用的 phone 前缀。若 DB 不可用会被自动跳过。
"""

import os
import time
from datetime import timedelta
from unittest.mock import patch

import jwt
import pyotp
import pytest

from app.auth import security
from app.auth.schemas import (
    CreateUserRequest,
    EnrollConfirmRequest,
    EnrollRequest,
    LoginRequest,
    UpdateUserRequest,
)

TEST_SECRET = "test-secret-key-do-not-use-in-prod-32bytes!"
TEST_PHONE_PREFIX = "139TEST"


@pytest.fixture(autouse=True)
def _override_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    from importlib import reload

    from app import config

    reload(config)
    from app.auth import security as sec

    reload(sec)
    yield
    reload(config)
    reload(sec)


def _fresh_phone() -> str:
    return f"{TEST_PHONE_PREFIX}{int(time.time() * 1000) % 100000:05d}"


class TestSecurityPure:
    def test_totp_secret_is_base32(self):
        s = security.generate_totp_secret()
        assert len(s) == 32
        # base32 字符集
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in s)

    def test_totp_verify_current_code(self):
        s = security.generate_totp_secret()
        code = pyotp.TOTP(s).now()
        assert security.verify_totp(s, code) is True

    def test_totp_verify_rejects_wrong_code(self):
        s = security.generate_totp_secret()
        # '000000' 命中概率 1/1e6，多试几个几乎不可能全部命中
        rejected = [security.verify_totp(s, "000000") for _ in range(5)]
        assert all(r is False for r in rejected)

    def test_invitation_code_format(self):
        codes = [security.generate_invitation_code() for _ in range(20)]
        for c in codes:
            assert len(c) == 6
            # 实际字母表 ABCDEFGHJKLMNPQRSTUVWXYZ23456789 只排除 I/O/0/1
            for ch in c:
                assert ch not in "01IO"
        # 随机性：20 个里至少有 2 个不同
        assert len(set(codes)) >= 2

    def test_jwt_access_token_round_trip(self):
        token = security.create_access_token(42, "admin")
        payload = security.decode_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_jwt_refresh_token_type(self):
        token = security.create_refresh_token(42)
        payload = security.decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == "42"

    def test_jwt_pending_token_type(self):
        token = security.create_pending_token(42)
        payload = security.decode_token(token)
        assert payload["type"] == "pending"

    def test_jwt_expired_token_raises(self):
        with patch("app.auth.security.settings") as mock_settings:
            mock_settings.jwt_secret_key = TEST_SECRET
            mock_settings.jwt_algorithm = "HS256"
            mock_settings.access_token_expire_minutes = -1  # 已过期
            from app.auth.security import _create_token

            token = _create_token({"sub": "1"}, timedelta(minutes=-1), "access")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            security.decode_token(token)
        assert exc_info.value.status_code == 401

    def test_jwt_tampered_token_raises(self):
        token = security.create_access_token(1, "user")
        # 翻转最后一位（破坏签名）
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            security.decode_token(tampered)

    def test_jwt_wrong_secret_raises(self):
        token = jwt.encode(
            {"sub": "1", "type": "access"}, "different-secret", algorithm="HS256"
        )
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            security.decode_token(token)

    def test_hash_token_deterministic(self):
        assert security.hash_token("abc") == security.hash_token("abc")
        assert security.hash_token("abc") != security.hash_token("abd")

    def test_hash_token_length(self):
        # SHA256 hex = 64 chars
        assert len(security.hash_token("anything")) == 64

    def test_qrcode_data_uri_format(self):
        uri = security.build_totp_uri("13800138000", "JBSWY3DPEHPK3PXP")
        data_uri = security.totp_qrcode_data_uri(uri)
        assert data_uri.startswith("data:image/png;base64,")

    def test_build_totp_uri_contains_issuer(self):
        uri = security.build_totp_uri("13800138000", "JBSWY3DPEHPK3PXP")
        assert "otpauth://totp/" in uri
        assert "13800138000" in uri

    def test_cookie_names_are_stable(self):
        # 前端和 WebSocket 都依赖这些字符串字面量
        assert security.ACCESS_COOKIE == "access_token"
        assert security.REFRESH_COOKIE == "refresh_token"


class TestSchemas:
    def test_login_request_valid(self):
        req = LoginRequest(phone="13800138000", totp_code="123456")
        assert req.phone == "13800138000"

    def test_login_request_rejects_short_totp(self):
        with pytest.raises(Exception):
            LoginRequest(phone="13800138000", totp_code="12345")

    def test_login_request_rejects_short_phone(self):
        with pytest.raises(Exception):
            LoginRequest(phone="138", totp_code="123456")

    def test_enroll_request_valid(self):
        req = EnrollRequest(phone="13800138000", invitation_code="ABC123")
        assert req.invitation_code == "ABC123"

    def test_enroll_confirm_request_valid(self):
        req = EnrollConfirmRequest(pending_token="xxx", totp_code="123456")
        assert req.pending_token == "xxx"

    def test_create_user_request_validates_role(self):
        CreateUserRequest(phone="13800138000", role="user")
        CreateUserRequest(phone="13800138000", role="admin")
        with pytest.raises(Exception):
            CreateUserRequest(phone="13800138000", role="superadmin")

    def test_update_user_request_allows_partial(self):
        req = UpdateUserRequest(is_active=False)
        assert req.is_active is False
        assert req.reset_totp is None


# --- DB 集成测试 ---


async def _can_connect_db() -> bool:
    try:
        from app.database import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture
async def db_available():
    return await _can_connect_db()


class TestUserServiceDB:
    """UserService 集成测试，需要本地 PostgreSQL。"""

    @pytest.mark.asyncio
    async def test_create_user_and_login_flow(self, db_available):
        if not db_available:
            pytest.skip("DB 不可用")

        from app.auth.service import UserService
        from app.database import async_session

        phone = _fresh_phone()
        async with async_session() as db:
            svc = UserService(db)
            user = await svc.create_user(phone, role="user")
            assert user.role == "user"
            assert user.totp_secret is None
            assert user.invitation_code is not None
            assert len(user.invitation_code) == 6

            # begin enrollment
            invitation = user.invitation_code
            user = await svc.begin_enrollment(phone, invitation)
            assert user.totp_secret is not None

            # confirm enrollment with valid TOTP
            code = pyotp.TOTP(user.totp_secret).now()
            user = await svc.confirm_enrollment(user, code)
            assert user.enrolled_at is not None
            assert user.invitation_code is None

            # login with valid TOTP
            code2 = pyotp.TOTP(user.totp_secret).now()
            logged_in = await svc.login(phone, code2)
            assert logged_in.last_login_at is not None

            # login with wrong TOTP fails
            with pytest.raises(ValueError):
                await svc.login(phone, "000000")

            # refresh token round-trip
            raw, _ = await svc.issue_refresh_token(user.id)
            verified = await svc.verify_refresh_token(raw)
            assert verified is not None
            assert verified.id == user.id

            # revoke and verify fails
            await svc.revoke_refresh_token(raw)
            assert await svc.verify_refresh_token(raw) is None

            # cleanup
            await db.delete(user)
            await db.commit()
