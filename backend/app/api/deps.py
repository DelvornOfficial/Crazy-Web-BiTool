from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.admin import Admin

security_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """
    Extracts client IP safely.
    Checks X-Forwarded-For and X-Real-IP for Nginx / reverse proxy deployment on VPS.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host
    return "127.0.0.1"


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """
    Validates JWT token and fetches active admin record using parameterized ORM query.
    100% Anti-SQL Injection proof.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired or tampered access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin_id_str = payload.get("sub")
    if not admin_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
        )

    try:
        admin_id = int(admin_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject claim format",
        )

    # Parameterized query (Anti-SQL Injection)
    stmt = select(Admin).where(Admin.id == admin_id)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account not found",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is disabled",
        )

    return admin


async def require_superadmin(
    current_admin: Admin = Depends(get_current_admin),
) -> Admin:
    """
    Enforces Role-Based Access Control (RBAC) - Superadmin only.
    """
    if current_admin.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient administrative privileges",
        )
    return current_admin
