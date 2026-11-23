from fastapi import APIRouter, Depends, Request, responses, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.app_release import AppRelease
from app.models.download_log import DownloadLog
from app.api.deps import get_client_ip

router = APIRouter(prefix="/downloads", tags=["Download Tracking"])


@router.get("/apk")
async def download_apk(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Public Endpoint:
    Tracks APK download, records telemetry analytics,
    increments release download counter, and redirects to target APK URL.
    If no APK is linked, returns 404 with 'APK Not Linked'.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown")[:512]

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

    # Increment download counter
    release.download_count += 1

    # Log analytics telemetry
    log_entry = DownloadLog(
        release_id=release.id,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.add(log_entry)
    await db.commit()

    if release.download_url.startswith("http"):
        return responses.RedirectResponse(url=release.download_url, status_code=status.HTTP_302_FOUND)

    # For local static uploads (/static/uploads/apks/...)
    if release.download_url.startswith("/"):
        return responses.RedirectResponse(url=release.download_url, status_code=status.HTTP_302_FOUND)

    return {
        "status": "success",
        "version": release.version,
        "download_url": release.download_url,
    }
