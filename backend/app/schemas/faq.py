from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FaqBase(BaseModel):
    question: str = Field(..., min_length=3, max_length=512)
    answer: str = Field(..., min_length=3)
    display_order: int = Field(1, ge=0)
    is_active: bool = Field(True)


class FaqCreate(FaqBase):
    pass


class FaqUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=3, max_length=512)
    answer: Optional[str] = Field(None, min_length=3)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class FaqResponse(FaqBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

