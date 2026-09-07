from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    duration_minutes: int = Field(gt=0, le=480)
    price_minor: int = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    duration_minutes: int | None = Field(default=None, gt=0, le=480)
    price_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None


class ServiceOut(ServiceCreate):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}
