from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ShowcaseVideoCreate(BaseModel):
    title: str = Field("Showcase Video", min_length=2, max_length=128)
    video_url: str = Field(..., min_length=5, max_length=1024)
    poster_url: Optional[str] = Field(None, max_length=1024)
    duration_seconds: int = Field(60, ge=1, le=7200)
    display_order: int = Field(0, ge=0)
    is_active: bool = True

    model_config = ConfigDict(str_strip_whitespace=True)


class ShowcaseVideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=128)
    video_url: Optional[str] = Field(None, min_length=5, max_length=1024)
    poster_url: Optional[str] = Field(None, max_length=1024)
    duration_seconds: Optional[int] = Field(None, ge=1, le=7200)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ShowcaseVideoResponse(BaseModel):
    id: int
    title: str
    video_url: str
    poster_url: Optional[str] = None
    duration_seconds: int
    display_order: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
