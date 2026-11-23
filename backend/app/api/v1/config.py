from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.site_setting import SiteSetting
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.site_setting import SiteConfigResponse, SiteConfigUpdate
from app.api.deps import get_current_admin

router = APIRouter(prefix="/site", tags=["Site Global Configuration"])

DEFAULT_CONFIG = {
    "telegram_url": "",
    "brand_title": "",
    "support_text": "",
    "nav_btn1_text": "Showcase",
    "nav_btn1_link": "#showcase",
    "nav_btn2_text": "Installation",
    "nav_btn2_link": "#install",
    "nav_btn3_text": "FAQ",
    "nav_btn3_link": "#faq",
    "nav_tg_btn_text": "Join Telegram",
    "footer_copy_text": "",
    "show_app_details_card": "true",
    "custom_action_btn_text": "",
    "custom_action_btn_link": "",
    "buy_key_btn_text": "Buy Key Yourself",
    "buy_key_btn_link": "",
    "show_top_nav": "true",
    "show_join_tg_btn": "true",
    "join_tg_btn_text": "JOIN TG",
    "show_download_btn": "true",
    "download_btn_text": "DOWNLOAD APK",
    "show_install_guide": "true",
    "show_faq_section": "true",
    "show_footer": "true",
}


@router.get("/config", response_model=SiteConfigResponse)
async def get_site_config(
    db: AsyncSession = Depends(get_db),
):
    """
    Public Endpoint: Returns dynamic site configuration including Telegram channel link.
    """
    result = await db.execute(select(SiteSetting))
    settings_records = result.scalars().all()
    config_dict = dict(DEFAULT_CONFIG)

    for item in settings_records:
        if item.key in config_dict:
            config_dict[item.key] = item.value

    return SiteConfigResponse(**config_dict)


@router.put("/config", response_model=SiteConfigResponse)
async def update_site_config(
    payload: SiteConfigUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Endpoint: Update Telegram channel URL and site titles.
    """
    updates = payload.model_dump()
    for key, value in updates.items():
        stmt = select(SiteSetting).where(SiteSetting.key == key)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.value = str(value)
        else:
            new_record = SiteSetting(key=key, value=str(value))
            db.add(new_record)

    audit = AuditLog(
        admin_username=current_admin.username,
        action="UPDATE_SITE_CONFIG",
        ip_address="admin_action",
        details=f"Updated site settings: telegram_url='{payload.telegram_url}'",
        status="SUCCESS",
    )
    db.add(audit)

    await db.commit()

    # Trigger Realtime WebSocket broadcast
    from app.api.v1.websocket_sync import manager
    await manager.broadcast("CONFIG_UPDATED", updates)

    return SiteConfigResponse(**updates)

