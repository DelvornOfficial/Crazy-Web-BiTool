from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.core.database import Base


class AppFeature(Base):
    __tablename__ = "app_features"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(64), nullable=False)
    short_description = Column(String(255), nullable=False)
    icon_type = Column(String(32), default="check", nullable=False)  # "check", "shield", "zap", "refresh", "lock", "cpu"
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

