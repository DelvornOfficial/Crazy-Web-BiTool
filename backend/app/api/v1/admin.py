from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.models.admin import Admin
from app.models.app_release import AppRelease
from app.models.audit_log import AuditLog
from app.models.download_log import DownloadLog
from app.schemas.analytics import DashboardStats, AuditLogItem
from app.schemas.release import ReleaseResponse
from app.api.deps import get_current_admin, require_superadmin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard & System Monitoring"])


@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns real-time operational statistics for the Admin Dashboard:
    - Total downloads across all versions
    - Active releases count
    - Latest version string
    - Recent security audit logs
    """
    # Total downloads sum
    dl_stmt = select(func.sum(AppRelease.download_count))
    dl_res = await db.execute(dl_stmt)
    total_downloads = dl_res.scalar() or 0

    # Active releases
    rel_count_stmt = select(func.count(AppRelease.id)).where(AppRelease.is_active == True)
    rel_count_res = await db.execute(rel_count_stmt)
    active_releases_count = rel_count_res.scalar() or 0

    # Total audits
    audit_count_stmt = select(func.count(AuditLog.id))
    audit_count_res = await db.execute(audit_count_stmt)
    total_audit_events = audit_count_res.scalar() or 0

    # Recent releases
    recent_rel_stmt = select(AppRelease).order_by(desc(AppRelease.id)).limit(5)
    recent_rel_res = await db.execute(recent_rel_stmt)
    recent_releases = recent_rel_res.scalars().all()

    latest_version = recent_releases[0].version if recent_releases else "v2.4.0"

    # Recent audits
    recent_audit_stmt = select(AuditLog).order_by(desc(AuditLog.id)).limit(10)
    recent_audit_res = await db.execute(recent_audit_stmt)
    recent_audits = recent_audit_res.scalars().all()

    return DashboardStats(
        total_downloads=total_downloads,
        active_releases_count=active_releases_count,
        latest_version=latest_version,
        total_audit_events=total_audit_events,
        recent_releases=[ReleaseResponse.model_validate(r) for r in recent_releases],
        recent_audits=[AuditLogItem.model_validate(a) for a in recent_audits],
    )


@router.get("/audit-logs", response_model=List[AuditLogItem])
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated security and access audit logs.
    """
    stmt = select(AuditLog).order_by(desc(AuditLog.id)).offset(offset).limit(min(limit, 100))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/unlock-account/{username}")
async def unlock_account(
    username: str,
    current_admin: Admin = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Superadmin action: Force-unlock an account locked due to failed attempts.
    """
    stmt = select(Admin).where(Admin.username == username)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin user '{username}' not found",
        )

    admin.locked_until = None
    admin.failed_login_attempts = 0

    audit_entry = AuditLog(
        admin_username=current_admin.username,
        action="MANUAL_ACCOUNT_UNLOCK",
        ip_address="internal",
        details=f"Superadmin unlocked account '{username}'",
        status="SUCCESS",
    )
    db.add(audit_entry)
    await db.commit()

    return {"status": "success", "message": f"Account '{username}' has been unlocked"}
