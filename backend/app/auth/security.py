import base64
import hashlib
import io
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import pyotp
import qrcode
from fastapi import HTTPException, Response, status

from app.config import get_settings

settings = get_settings()

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(phone: str, secret: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=phone, issuer_name="小麦国度")


def verify_totp(secret: str, code: str) -> bool:
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:
        return False


def totp_qrcode_data_uri(uri: str) -> str:
    buf = io.BytesIO()
    qrcode.make(uri).save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def generate_invitation_code() -> str:
    # 排除 0/O/1/I 等易混字符，避免人工转录错误
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _create_token(payload: dict, expires_delta: timedelta, token_type: str) -> str:
    data = {
        **payload,
        "type": token_type,
        "jti": secrets.token_hex(16),
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        {"sub": str(user_id), "role": role},
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


def create_pending_token(user_id: int) -> str:
    # 注册流程专用：10 分钟有效，仅能用于 /auth/enroll/confirm 一次
    return _create_token({"sub": str(user_id)}, timedelta(minutes=10), "pending")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _cookie_common_kwargs() -> dict:
    kwargs = {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
    }
    if settings.cookie_domain:
        kwargs["domain"] = settings.cookie_domain
    return kwargs


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    common = _cookie_common_kwargs()
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
        **common,
    )
    # Refresh cookie 限定在 /api/v1/auth 路径下，减少其他请求中暴露
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=settings.refresh_token_expire_days * 86400,
        path=f"{settings.api_v1_prefix}/auth",
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    common = _cookie_common_kwargs()
    response.delete_cookie(ACCESS_COOKIE, path="/", **common)
    response.delete_cookie(
        REFRESH_COOKIE, path=f"{settings.api_v1_prefix}/auth", **common
    )
