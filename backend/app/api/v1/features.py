from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc

from app.core.database import get_db
from app.models.app_feature import AppFeature
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.app_feature import (
    AppFeatureCreate,
    AppFeatureUpdate,
    AppFeatureResponse,
)
from app.api.deps import get_current_admin

router = APIRouter(prefix="/features", tags=["App Dynamic Features"])


@router.get("", response_model=List[AppFeatureResponse])
async def list_features_public(
    db: AsyncSession = Depends(get_db),
):
    """
    Public Endpoint: Returns active app features for showcase card.
    """
    stmt = (
        select(AppFeature)
        .where(AppFeature.is_active == True)
        .order_by(asc(AppFeature.display_order), asc(AppFeature.id))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/all", response_model=List[AppFeatureResponse])
async def list_features_admin(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Returns all features (active & archived).
    """
    stmt = select(AppFeature).order_by(asc(AppFeature.display_order), asc(AppFeature.id))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AppFeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    payload: AppFeatureCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Create a new app feature with title and short description.
    """
    feature = AppFeature(
        title=payload.title,
        short_description=payload.short_description,
        icon_type=payload.icon_type,
        display_order=payload.display_order,
        is_active=payload.is_active,
    )
    db.add(feature)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="CREATE_FEATURE",
        ip_address="admin_action",
        details=f"Created feature '{payload.title}': {payload.short_description}",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(feature)

    from app.api.v1.websocket_sync import manager
    await manager.broadcast("FEATURES_UPDATED", {"id": feature.id})

    return feature


@router.patch("/{feature_id}", response_model=AppFeatureResponse)
async def update_feature(
    feature_id: int,
    payload: AppFeatureUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Update feature title, description, or status.
    """
    stmt = select(AppFeature).where(AppFeature.id == feature_id)
    result = await db.execute(stmt)
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feature, key, value)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="UPDATE_FEATURE",
        ip_address="admin_action",
        details=f"Updated feature ID {feature_id} ('{feature.title}')",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(feature)

    from app.api.v1.websocket_sync import manager
    await manager.broadcast("FEATURES_UPDATED", {"id": feature.id})

    return feature


@router.delete("/{feature_id}")
async def delete_feature(
    feature_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Delete an app feature.
    """
    stmt = select(AppFeature).where(AppFeature.id == feature_id)
    result = await db.execute(stmt)
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )

    title_str = feature.title
    await db.delete(feature)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="DELETE_FEATURE",
        ip_address="admin_action",
        details=f"Deleted feature ID {feature_id} ('{title_str}')",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    return {"status": "success", "message": f"Feature '{title_str}' deleted successfully"}

