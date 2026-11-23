from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.release import ReleaseResponse


class AuditLogItem(BaseModel):
    id: int
    admin_username: str
    action: str
    ip_address: str
    details: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_downloads: int
    active_releases_count: int
    latest_version: str
    total_audit_events: int
    recent_releases: List[ReleaseResponse]
    recent_audits: List[AuditLogItem]
