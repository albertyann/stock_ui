from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=4, max_length=20)
    totp_code: str = Field(..., min_length=6, max_length=6)


class EnrollRequest(BaseModel):
    phone: str = Field(..., min_length=4, max_length=20)
    invitation_code: str = Field(..., min_length=4, max_length=16)


class EnrollConfirmRequest(BaseModel):
    pending_token: str
    totp_code: str = Field(..., min_length=6, max_length=6)


class CreateUserRequest(BaseModel):
    phone: str = Field(..., min_length=4, max_length=20)
    role: str = Field("user", pattern="^(admin|user)$")


class UpdateUserRequest(BaseModel):
    is_active: bool | None = None
    reset_totp: bool | None = None
