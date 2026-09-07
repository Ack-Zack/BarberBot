from pydantic import BaseModel, Field


class OnboardingStatus(BaseModel):
    needs_business: bool
    business_id: int | None
    business_name: str | None
    owner_member_id: int | None
    has_service: bool
    has_working_hours: bool
    complete: bool
    booking_link: str | None


class JoinBusinessOut(BaseModel):
    business_id: int
    business_name: str
    role: str
