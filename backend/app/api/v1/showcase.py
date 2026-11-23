import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc

from app.core.database import get_db
from app.models.showcase_video import ShowcaseVideo
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.showcase_video import (
    ShowcaseVideoCreate,
    ShowcaseVideoUpdate,
    ShowcaseVideoResponse,
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/showcase", tags=["Showcase Video & Playlist"])

# Directory where locally uploaded videos are securely stored
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads", "videos"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v"}


@router.get("/stream/{video_id}")
async def stream_video_protected(
    video_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Protected Byte-Range Video Streaming Endpoint:
    Hides direct filesystem and file storage paths.
    Supports HTTP 206 Partial Content for smooth HTML5 video scrubbing and seeking.
    """
    stmt = select(ShowcaseVideo).where(ShowcaseVideo.id == video_id)
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video stream not found")

    if not video.video_url or not video.video_url.startswith("/static/uploads/videos/"):
        # Remote external URL
        raise HTTPException(status_code=400, detail="External video streaming not hosted locally")

    filename = os.path.basename(video.video_url)
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Video binary file not found on disk")

    file_size = os.path.getsize(filepath)
    range_header = request.headers.get("range")

    content_type = "video/mp4"
    if filename.endswith(".webm"):
        content_type = "video/webm"
    elif filename.endswith(".mkv"):
        content_type = "video/x-matroska"

    if range_header:
        byte1, byte2 = 0, None
        try:
            match = range_header.replace("bytes=", "").split("-")
            if match[0]:
                byte1 = int(match[0])
            if len(match) > 1 and match[1]:
                byte2 = int(match[1])
        except Exception:
            byte1, byte2 = 0, None

        if byte1 >= file_size:
            raise HTTPException(
                status_code=416,
                detail="Requested range not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        # Standard streaming chunk size (1MB to 2MB)
        target_chunk_size = 1024 * 1024 * 2
        if byte2 is not None and byte2 >= byte1:
            end_byte = min(byte2, file_size - 1)
        else:
            end_byte = min(byte1 + target_chunk_size - 1, file_size - 1)

        content_length = end_byte - byte1 + 1

        def iterfile():
            with open(filepath, "rb") as f:
                f.seek(byte1)
                remaining = content_length
                while remaining > 0:
                    chunk = f.read(min(remaining, 64 * 1024))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        headers = {
            "Content-Range": f"bytes {byte1}-{end_byte}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff"
        }
        return StreamingResponse(iterfile(), status_code=206, headers=headers)
    else:
        def iter_full():
            with open(filepath, "rb") as f:
                while chunk := f.read(64 * 1024):
                    yield chunk

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff"
        }
        return StreamingResponse(iter_full(), status_code=200, headers=headers)


@router.get("/videos", response_model=List[ShowcaseVideoResponse])
async def list_showcase_videos(
    db: AsyncSession = Depends(get_db),
):
    """
    Public Endpoint: Returns all active showcase videos in display order.
    Consumable by frontend for continuous multi-video auto-advance playback.
    Direct storage paths are completely masked.
    """
    stmt = (
        select(ShowcaseVideo)
        .where(ShowcaseVideo.is_active == True)
        .order_by(asc(ShowcaseVideo.display_order), asc(ShowcaseVideo.id))
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    out = []
    for r in records:
        masked_url = f"/api/v1/showcase/stream/{r.id}" if r.video_url.startswith("/static/uploads/videos/") else r.video_url
        out.append(ShowcaseVideoResponse(
            id=r.id,
            title=r.title,
            video_url=masked_url,
            poster_url=r.poster_url,
            duration_seconds=r.duration_seconds,
            display_order=r.display_order,
            is_active=r.is_active,
            created_at=r.created_at
        ))
    return out


@router.get("/all-videos", response_model=List[ShowcaseVideoResponse])
async def list_all_videos_admin(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Returns all videos (active and inactive).
    """
    stmt = select(ShowcaseVideo).order_by(asc(ShowcaseVideo.display_order), asc(ShowcaseVideo.id))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/upload-video", response_model=ShowcaseVideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_showcase_video(
    file: UploadFile = File(...),
    title: str = Form("Showcase Video"),
    duration_seconds: int = Form(30),
    display_order: int = Form(1),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Upload video directly from local storage.
    Thumbnail removed per user request.
    """
    filename = file.filename or "video.mp4"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Generate collision-free safe filename
    safe_filename = f"{uuid.uuid4().hex[:12]}_{abs(hash(filename)) % 100000}{ext}"
    target_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video to disk: {str(e)}",
        )
    finally:
        await file.close()

    # Direct static path
    video_url = f"/static/uploads/videos/{safe_filename}"

    video = ShowcaseVideo(
        title=title,
        video_url=video_url,
        poster_url=None,  # Thumbnail removed per user request
        duration_seconds=duration_seconds,
        display_order=display_order,
        is_active=True,
    )
    db.add(video)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="UPLOAD_SHOWCASE_VIDEO",
        ip_address="admin_action",
        details=f"Uploaded local video '{title}' ({safe_filename})",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(video)
    return video


@router.post("/videos", response_model=ShowcaseVideoResponse, status_code=status.HTTP_201_CREATED)
async def add_showcase_video(
    payload: ShowcaseVideoCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Add a video to playlist via URL.
    """
    video = ShowcaseVideo(
        title=payload.title,
        video_url=payload.video_url,
        poster_url=None,  # Thumbnail removed per user request
        duration_seconds=payload.duration_seconds,
        display_order=payload.display_order,
        is_active=payload.is_active,
    )
    db.add(video)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="ADD_SHOWCASE_VIDEO",
        ip_address="admin_action",
        details=f"Added video to playlist: '{payload.title}' ({payload.video_url})",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(video)
    return video


@router.delete("/videos/{video_id}")
async def delete_showcase_video(
    video_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Delete a video from the showcase playlist & remove local file if stored.
    """
    stmt = select(ShowcaseVideo).where(ShowcaseVideo.id == video_id)
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showcase video not found",
        )

    # Clean up local disk file if uploaded locally
    if video.video_url and "/static/uploads/videos/" in video.video_url:
        filename = video.video_url.split("/")[-1]
        local_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

    title_str = video.title
    await db.delete(video)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="DELETE_SHOWCASE_VIDEO",
        ip_address="admin_action",
        details=f"Deleted video ID {video_id} ('{title_str}')",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    return {"status": "success", "message": f"Video '{title_str}' deleted successfully"}
