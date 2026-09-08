from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1, max_length=10000)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
