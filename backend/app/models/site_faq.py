from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class SiteFaq(Base):
    __tablename__ = "site_faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(512), nullable=False)
    answer = Column(Text, nullable=False)
    display_order = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

