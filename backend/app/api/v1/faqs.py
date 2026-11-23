from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.site_faq import SiteFaq
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.faq import FaqCreate, FaqUpdate, FaqResponse
from app.api.deps import get_current_admin

router = APIRouter(prefix="/faqs", tags=["Site FAQ Management"])


@router.get("/active", response_model=List[FaqResponse])
async def list_active_faqs(
    db: AsyncSession = Depends(get_db),
):
    """
    Public Endpoint: Returns all active FAQs ordered by display order.
    """
    stmt = select(SiteFaq).where(SiteFaq.is_active == True).order_by(SiteFaq.display_order.asc(), SiteFaq.id.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/all", response_model=List[FaqResponse])
async def list_all_faqs(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Returns all FAQs for management.
    """
    stmt = select(SiteFaq).order_by(SiteFaq.display_order.asc(), SiteFaq.id.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=FaqResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    payload: FaqCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Add new FAQ item.
    """
    new_faq = SiteFaq(
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        display_order=payload.display_order,
        is_active=payload.is_active,
    )
    db.add(new_faq)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="CREATE_FAQ",
        ip_address="admin_action",
        details=f"Created FAQ: '{payload.question[:40]}...'",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_faq)

    from app.api.v1.websocket_sync import manager
    await manager.broadcast("FAQS_UPDATED", {"id": new_faq.id})

    return new_faq


@router.delete("/{faq_id}")
async def delete_faq(
    faq_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Delete FAQ item.
    """
    stmt = select(SiteFaq).where(SiteFaq.id == faq_id)
    res = await db.execute(stmt)
    faq = res.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    q_title = faq.question
    await db.delete(faq)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="DELETE_FAQ",
        ip_address="admin_action",
        details=f"Deleted FAQ '{q_title[:40]}...'",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()
    return {"status": "success", "message": "FAQ deleted"}

