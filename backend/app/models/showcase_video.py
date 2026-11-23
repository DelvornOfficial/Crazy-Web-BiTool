from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.core.database import Base


class ShowcaseVideo(Base):
    __tablename__ = "showcase_videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), default="Showcase Video", nullable=False)
    video_url = Column(String(1024), nullable=False)
    poster_url = Column(String(1024), nullable=True)
    duration_seconds = Column(Integer, default=60, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
