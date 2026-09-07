from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


AppointmentStatus = Literal["pending", "confirmed", "completed", "cancelled", "no_show"]


class AppointmentCreate(BaseModel):
    barber_id: int
    service_id: int
    starts_at: datetime
    client_id: int | None = None
    client_name: str | None = Field(default=None, max_length=255)
    client_phone: str | None = Field(default=None, max_length=32)

    @field_validator("client_name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class AppointmentUpdate(BaseModel):
    starts_at: datetime | None = None
    status: AppointmentStatus | None = None


class AppointmentOut(BaseModel):
    id: int
    barber_id: int
    client_id: int
    service_id: int
    starts_at: datetime
    ends_at: datetime
    status: str
    price_minor: int
    duration_minutes: int
    cancelled_at: datetime | None = None
    barber_name: str | None = None
    client_name: str | None = None
    service_name: str | None = None


class AvailabilityOut(BaseModel):
    date: str
    timezone: str
    barber_id: int
    service_id: int
    slots: list[str]
