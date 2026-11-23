from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime
from app.core.database import Base


class AppRelease(Base):
    __tablename__ = "app_releases"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(32), unique=True, index=True, nullable=False)  # e.g. "v2.4.0"
    title = Column(String(128), default="Next Level Cheat APK", nullable=False)
    download_url = Column(String(512), nullable=False)
    file_size_mb = Column(Float, default=45.0, nullable=False)
    min_android_version = Column(String(32), default="Android 8.0+", nullable=False)
    changelog = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
