from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AppFeatureBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=64)
    short_description: str = Field(..., min_length=3, max_length=255)
    icon_type: str = Field("check", max_length=32)
    display_order: int = Field(0, ge=0)
    is_active: bool = True

    model_config = ConfigDict(str_strip_whitespace=True)


class AppFeatureCreate(AppFeatureBase):
    pass


class AppFeatureUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=64)
    short_description: Optional[str] = Field(None, min_length=3, max_length=255)
    icon_type: Optional[str] = Field(None, max_length=32)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(str_strip_whitespace=True)


class AppFeatureResponse(AppFeatureBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

