from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import schemas, security
from app.auth.dependencies import get_current_user, require_admin
from app.auth.security import REFRESH_COOKIE
from app.auth.service import UserService
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_payload(user: User, include_invitation: bool = False) -> dict:
    return {
        "id": user.id,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "has_totp": user.totp_secret is not None,
        "enrolled_at": user.enrolled_at.isoformat() if user.enrolled_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "invitation_code": user.invitation_code if include_invitation else None,
    }


@router.post("/login")
async def login(
    body: schemas.LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    try:
        user = await svc.login(body.phone, body.totp_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    access = security.create_access_token(user.id, user.role)
    refresh, _ = await svc.issue_refresh_token(user.id)
    security.set_auth_cookies(response, access, refresh)
    return {"success": True, "data": _user_payload(user)}


@router.post("/enroll")
async def enroll(body: schemas.EnrollRequest, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    try:
        user = await svc.begin_enrollment(body.phone, body.invitation_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    pending = security.create_pending_token(user.id)
    uri = security.build_totp_uri(user.phone, user.totp_secret)
    return {
        "success": True,
        "data": {
            "pending_token": pending,
            "qr_code_data_uri": security.totp_qrcode_data_uri(uri),
            "totp_uri": uri,
            "secret": user.totp_secret,
        },
    }


@router.post("/enroll/confirm")
async def enroll_confirm(
    body: schemas.EnrollConfirmRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    payload = security.decode_token(body.pending_token)
    if payload.get("type") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的注册令牌"
        )
    svc = UserService(db)
    user = await svc.get_by_id(int(payload["sub"]))
    if not user or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户不在待绑定状态"
        )
    try:
        user = await svc.confirm_enrollment(user, body.totp_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    access = security.create_access_token(user.id, user.role)
    refresh, _ = await svc.issue_refresh_token(user.id)
    security.set_auth_cookies(response, access, refresh)
    return {"success": True, "data": _user_payload(user)}


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无刷新令牌"
        )
    svc = UserService(db)
    user = await svc.verify_refresh_token(raw)
    if not user:
        security.clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效或已过期"
        )
    # 轮换：旧的撤销，签发新对
    await svc.revoke_refresh_token(raw)
    access = security.create_access_token(user.id, user.role)
    new_refresh, _ = await svc.issue_refresh_token(user.id)
    security.set_auth_cookies(response, access, new_refresh)
    return {"success": True, "data": _user_payload(user)}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        svc = UserService(db)
        await svc.revoke_refresh_token(raw)
    security.clear_auth_cookies(response)
    return {"success": True}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"success": True, "data": _user_payload(user)}


# --- 管理员接口 ---
@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    users = await svc.list_users()
    return {
        "success": True,
        "data": [_user_payload(u, include_invitation=True) for u in users],
    }


@router.post("/users", dependencies=[Depends(require_admin)])
async def create_user(
    body: schemas.CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    try:
        user = await svc.create_user(body.phone, body.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {
        "success": True,
        "data": _user_payload(user, include_invitation=True),
    }


@router.patch("/users/{user_id}", dependencies=[Depends(require_admin)])
async def update_user(
    user_id: int,
    body: schemas.UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user: User | None = None
    try:
        if body.is_active is not None:
            user = await svc.update_active(user_id, body.is_active)
        if body.reset_totp:
            user = await svc.reset_totp(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if user is None:
        user = await svc.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )
    return {
        "success": True,
        "data": _user_payload(user, include_invitation=True),
    }
