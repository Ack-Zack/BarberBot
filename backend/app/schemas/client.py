from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=5000)


class ClientOut(ClientCreate):
    id: int
    user_id: int | None
    appointments_count: int = 0
    last_appointment_at: str | None = None

    model_config = {"from_attributes": True}
