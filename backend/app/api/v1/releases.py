import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.app_release import AppRelease
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.release import ReleaseCreate, ReleaseUpdate, ReleaseResponse
from app.api.deps import get_current_admin

router = APIRouter(prefix="/releases", tags=["App Releases Management"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads", "apks")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-apk", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_apk_release(
    file: UploadFile = File(...),
    version: str = Form(...),
    title: str = Form("Next Level Cheat APK"),
    min_android_version: str = Form("Android 8.0+"),
    changelog: Optional[str] = Form(""),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Upload an APK file directly from computer/storage, save to static directory,
    calculate size automatically, record in database, and link to downloads.
    """
    version_clean = version.strip()
    if not version_clean:
        raise HTTPException(status_code=400, detail="Version tag is required")

    # Verify duplicate version
    stmt = select(AppRelease).where(AppRelease.version == version_clean)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Release version {version_clean} already exists. Please choose a new version tag.",
        )

    # Validate filename extension
    filename = file.filename or "app.apk"
    if not filename.lower().endswith(".apk"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a valid .apk file.",
        )

    # Generate unique safe file name
    clean_base = "".join(c for c in os.path.splitext(filename)[0] if c.isalnum() or c in ("-", "_"))
    safe_name = f"{uuid.uuid4().hex[:8]}_{clean_base}.apk"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Read and save file chunks
    file_size_bytes = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024 * 4):  # 4MB chunks
            f.write(chunk)
            file_size_bytes += len(chunk)

    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    relative_download_url = f"/static/uploads/apks/{safe_name}"

    # Deactivate previous releases if this is the active release
    # (or set as new active release)
    new_release = AppRelease(
        version=version_clean,
        title=title.strip() if title else "Next Level Cheat APK",
        download_url=relative_download_url,
        file_size_mb=file_size_mb,
        min_android_version=min_android_version.strip() if min_android_version else "Android 8.0+",
        changelog=changelog.strip() if changelog else "",
        is_active=True,
    )
    db.add(new_release)

    # Audit log
    audit_entry = AuditLog(
        admin_username=current_admin.username,
        action="UPLOAD_APK_RELEASE",
        ip_address="admin_action",
        details=f"Uploaded APK {safe_name} ({file_size_mb} MB) for release {version_clean}",
        status="SUCCESS",
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(new_release)

    # Realtime WebSocket broadcast
    from app.api.v1.websocket_sync import manager
    await manager.broadcast("RELEASE_UPDATED", {"version": new_release.version})

    return new_release


@router.get("/latest", response_model=ReleaseResponse)
async def get_latest_active_release(
    db: AsyncSession = Depends(get_db),
):
    """
    Public Endpoint: Returns the latest active Next Level Cheat release.
    If no active release is found or APK is not linked, raises 404 with 'APK Not Linked'.
    """
    stmt = (
        select(AppRelease)
        .where(AppRelease.is_active == True)
        .order_by(desc(AppRelease.id))
        .limit(1)
    )
    result = await db.execute(stmt)
    release = result.scalar_one_or_none()

    if not release or not release.download_url or not release.download_url.strip():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="APK Not Linked",
        )

    return release


@router.get("", response_model=List[ReleaseResponse])
async def list_all_releases(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Returns all releases (active and archived).
    """
    stmt = select(AppRelease).order_by(desc(AppRelease.id))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
async def create_release(
    payload: ReleaseCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Publish a new Next Level Cheat release.
    """
    stmt = select(AppRelease).where(AppRelease.version == payload.version)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Release version {payload.version} already exists",
        )

    new_release = AppRelease(
        version=payload.version,
        title=payload.title,
        download_url=payload.download_url,
        file_size_mb=payload.file_size_mb,
        min_android_version=payload.min_android_version,
        changelog=payload.changelog,
        is_active=payload.is_active,
    )
    db.add(new_release)

    # Audit log
    audit_entry = AuditLog(
        admin_username=current_admin.username,
        action="CREATE_RELEASE",
        ip_address="admin_action",
        details=f"Created release {payload.version} ({payload.title})",
        status="SUCCESS",
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(new_release)

    # Realtime WebSocket broadcast
    from app.api.v1.websocket_sync import manager
    await manager.broadcast("RELEASE_UPDATED", {"version": new_release.version})

    return new_release


@router.patch("/{release_id}", response_model=ReleaseResponse)
async def update_release(
    release_id: int,
    payload: ReleaseUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Update release properties, download URL, or status.
    """
    stmt = select(AppRelease).where(AppRelease.id == release_id)
    result = await db.execute(stmt)
    release = result.scalar_one_or_none()

    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Release not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(release, key, value)

    # Audit log
    audit_entry = AuditLog(
        admin_username=current_admin.username,
        action="UPDATE_RELEASE",
        ip_address="admin_action",
        details=f"Updated release {release.version} fields: {list(update_data.keys())}",
        status="SUCCESS",
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(release)
    return release


@router.delete("/{release_id}")
async def delete_release(
    release_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Delete an added APK release.
    """
    stmt = select(AppRelease).where(AppRelease.id == release_id)
    result = await db.execute(stmt)
    release = result.scalar_one_or_none()

    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Release not found",
        )

    version_str = release.version
    await db.delete(release)

    # Audit log
    audit_entry = AuditLog(
        admin_username=current_admin.username,
        action="DELETE_RELEASE",
        ip_address="admin_action",
        details=f"Deleted release {version_str} (ID: {release_id})",
        status="SUCCESS",
    )
    db.add(audit_entry)

    await db.commit()
    return {"status": "success", "message": f"Release {version_str} deleted successfully"}
