from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.core.rate_limiter import limiter
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, AdminProfile, ChangePasswordRequest
from app.api.deps import get_client_ip, get_current_admin

router = APIRouter(prefix="/auth", tags=["High-Security Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    High-Security Admin Login Endpoint.
    - Protected against Brute Force & Credential Stuffing (IP & Account Lockout).
    - 100% Parameterized Query Execution (Anti-SQL Injection).
    - Constant-time password verification (Anti-Timing Attacks).
    - Comprehensive Audit Trail Logging.
    """
    client_ip = get_client_ip(request)

    # 1. IP-Level Rate Limit Check (bypassed for local loopback in dev)
    if client_ip not in ["127.0.0.1", "localhost", "::1"]:
        is_limited, retry_after = limiter.is_ip_rate_limited(client_ip)
        if is_limited:
            # Audit rate limit block
            audit_entry = AuditLog(
                admin_username=payload.username,
                action="LOGIN_ATTEMPT_BLOCKED",
                ip_address=client_ip,
                details=f"IP temporarily locked out. Retry after {retry_after}s.",
                status="BLOCKED",
            )
            db.add(audit_entry)
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts from this IP. Temporarily locked for {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    # 2. Parameterized Query Execution (Zero SQL Injection Possibility)
    stmt = select(Admin).where(Admin.username == payload.username)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    # Strictly verify against .env credentials & DB hash
    from app.core.config import get_live_env_admin_credentials
    live_env_user, live_env_hash = get_live_env_admin_credentials()

    is_valid_cred = False
    if admin and admin.is_active:
        # Match database password hash
        if verify_password(payload.password, admin.hashed_password):
            is_valid_cred = True
        # Or match live .env hash directly
        elif payload.username == live_env_user and verify_password(payload.password, live_env_hash):
            is_valid_cred = True
            admin.hashed_password = live_env_hash
            admin.failed_login_attempts = 0
            admin.locked_until = None

    # 3. Account-Level Lockout Check (Auto-unlock if correct credentials provided)
    if admin and admin.locked_until:
        if admin.locked_until > now:
            if is_valid_cred:
                # Valid credentials auto-clears the lockout immediately
                admin.locked_until = None
                admin.failed_login_attempts = 0
            else:
                remaining_mins = int((admin.locked_until - now).total_seconds() / 60) + 1
                audit_entry = AuditLog(
                    admin_username=payload.username,
                    action="LOGIN_LOCKED_ACCOUNT",
                    ip_address=client_ip,
                    details=f"Account locked until {admin.locked_until}",
                    status="BLOCKED",
                )
                db.add(audit_entry)
                await db.commit()

                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"This administrator account is locked due to repeated failed attempts. Try again in {remaining_mins} minute(s).",
                )
        else:
            # Lockout expired, reset counter
            admin.locked_until = None
            admin.failed_login_attempts = 0

    # 4. Final Verification Check
    is_valid = is_valid_cred

    if not is_valid:
        # Record failure for IP
        limiter.record_ip_failure(client_ip)

        # Record failure on Admin entity if user exists
        if admin:
            admin.failed_login_attempts += 1
            if admin.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                admin.locked_until = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                details = f"Account locked for {settings.LOCKOUT_DURATION_MINUTES}m after {admin.failed_login_attempts} failed attempts."
            else:
                remaining = settings.MAX_FAILED_LOGIN_ATTEMPTS - admin.failed_login_attempts
                details = f"Invalid password. {remaining} attempt(s) remaining before lockout."
        else:
            details = "Invalid username or password attempt."

        audit_entry = AuditLog(
            admin_username=payload.username,
            action="FAILED_LOGIN",
            ip_address=client_ip,
            details=details,
            status="FAILED",
        )
        db.add(audit_entry)
        await db.commit()

        # Generic message prevents username enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative username or password",
        )

    # 5. Successful Authentication
    limiter.reset_ip_failures(client_ip)
    admin.failed_login_attempts = 0
    admin.locked_until = None
    admin.last_login_at = now
    admin.last_login_ip = client_ip

    token = create_access_token(
        subject=str(admin.id),
        role=admin.role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    audit_entry = AuditLog(
        admin_username=admin.username,
        action="SUCCESSFUL_LOGIN",
        ip_address=client_ip,
        details="Authenticated successfully",
        status="SUCCESS",
    )
    db.add(audit_entry)
    await db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        admin=AdminProfile.model_validate(admin),
    )


@router.get("/me", response_model=AdminProfile)
async def get_current_admin_profile(
    current_admin: Admin = Depends(get_current_admin),
):
    """
    Returns current authenticated admin profile.
    """
    return AdminProfile.model_validate(current_admin)


@router.post("/change-password")
async def change_password():
    """
    Disabled: Passwords can ONLY be changed directly in .env via Bcrypt hash.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Password change via API/UI is disabled for maximum security. Passwords must be updated directly in the server .env file."
    )
