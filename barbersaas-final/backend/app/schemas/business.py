from datetime import datetime
from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    timezone: str = "Europe/Moscow"


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    timezone: str | None = None


class BusinessOut(BaseModel):
    id: int
    name: str
    slug: str
    timezone: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BookingLinkOut(BaseModel):
    url: str
