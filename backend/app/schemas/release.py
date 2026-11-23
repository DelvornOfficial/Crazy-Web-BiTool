from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ReleaseBase(BaseModel):
    version: str = Field(..., min_length=2, max_length=32, pattern=r"^v?[0-9]+\.[0-9]+(\.[0-9]+)?.*$")
    title: str = Field("Next Level Cheat APK", min_length=2, max_length=128)
    download_url: str = Field(..., min_length=5, max_length=512)
    file_size_mb: float = Field(..., gt=0, lt=2048)
    min_android_version: str = Field("Android 8.0+", max_length=32)
    changelog: Optional[str] = Field(None, max_length=2000)
    is_active: bool = True

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ReleaseCreate(ReleaseBase):
    pass


class ReleaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=128)
    download_url: Optional[str] = Field(None, min_length=5, max_length=512)
    file_size_mb: Optional[float] = Field(None, gt=0, lt=2048)
    min_android_version: Optional[str] = Field(None, max_length=32)
    changelog: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ReleaseResponse(ReleaseBase):
    id: int
    download_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
