from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    """
    High-Security Sanitized Admin Login Payload.
    Strict regex prevents SQL injection, command injection, and null-byte bypasses.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_\-\.]{3,32}$",
        description="Alphanumeric username (3-32 characters, safe characters only)",
    )
    password: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Admin secret password (minimum 3 characters)",
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AdminProfile(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    admin: AdminProfile


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=3, max_length=128)
    new_password: str = Field(..., min_length=3, max_length=128)

    model_config = ConfigDict(extra="forbid")
