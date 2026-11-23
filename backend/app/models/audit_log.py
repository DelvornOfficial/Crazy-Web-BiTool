from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_username = Column(String(64), index=True, nullable=False)
    action = Column(String(128), index=True, nullable=False)  # "LOGIN", "FAILED_LOGIN", "UPDATE_RELEASE", etc.
    ip_address = Column(String(45), nullable=False)
    details = Column(String(512), nullable=True)
    status = Column(String(32), default="SUCCESS", nullable=False)  # "SUCCESS", "FAILED", "BLOCKED"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
