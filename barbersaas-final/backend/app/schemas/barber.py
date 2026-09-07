from pydantic import BaseModel, Field


class BarberInviteCreate(BaseModel):
    expires_in_days: int = Field(default=7, ge=1, le=30)


class BarberInviteOut(BaseModel):
    url: str
    expires_at: str


class BarberOut(BaseModel):
    id: int
    display_name: str
    role: str
    is_active: bool
