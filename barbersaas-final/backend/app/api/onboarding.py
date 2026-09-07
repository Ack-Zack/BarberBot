from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import Business, BusinessMember, Client, Service, User, WorkingInterval
from app.schemas.onboarding import JoinBusinessOut, OnboardingStatus

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def make_booking_link(slug: str) -> str | None:
    username = settings.telegram_bot_username.strip().lstrip("@")
    if not username:
        return None
    start_param = quote(f"b_{slug}", safe="")
    return f"https://t.me/{username}?startapp={start_param}"


@router.get("/status", response_model=OnboardingStatus)
async def onboarding_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingStatus:
    membership = await db.scalar(
        select(BusinessMember)
        .where(BusinessMember.user_id == user.id, BusinessMember.is_active.is_(True))
        .order_by(BusinessMember.id)
        .limit(1)
    )
    if not membership:
        return OnboardingStatus(
            needs_business=True,
            business_id=None,
            business_name=None,
            owner_member_id=None,
            has_service=False,
            has_working_hours=False,
            complete=False,
            booking_link=None,
        )

    business = await db.get(Business, membership.business_id)
    if membership.role != "owner" or not business:
        return OnboardingStatus(
            needs_business=False,
            business_id=membership.business_id,
            business_name=business.name if business else None,
            owner_member_id=None,
            has_service=True,
            has_working_hours=True,
            complete=True,
            booking_link=make_booking_link(business.slug) if business else None,
        )

    service_count = await db.scalar(
        select(func.count(Service.id)).where(
            Service.business_id == membership.business_id,
            Service.is_active.is_(True),
        )
    )
    hours_count = await db.scalar(
        select(func.count(WorkingInterval.id)).where(
            WorkingInterval.barber_member_id == membership.id,
        )
    )
    has_service = bool(service_count)
    has_working_hours = bool(hours_count)
    return OnboardingStatus(
        needs_business=False,
        business_id=membership.business_id,
        business_name=business.name,
        owner_member_id=membership.id,
        has_service=has_service,
        has_working_hours=has_working_hours,
        complete=has_service and has_working_hours,
        booking_link=make_booking_link(business.slug),
    )


join_router = APIRouter(prefix="/businesses", tags=["businesses"])


@join_router.post("/join/{slug}", response_model=JoinBusinessOut)
async def join_business(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinBusinessOut:
    existing_membership = await db.scalar(
        select(BusinessMember)
        .where(BusinessMember.user_id == user.id, BusinessMember.is_active.is_(True))
        .order_by(BusinessMember.id)
        .limit(1)
    )
    if existing_membership:
        raise HTTPException(status_code=409, detail="User already belongs to a business")

    business = await db.scalar(select(Business).where(Business.slug == slug))
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    membership = BusinessMember(
        business_id=business.id,
        user_id=user.id,
        role="client",
        display_name=user.first_name,
        is_active=True,
    )
    db.add(membership)
    existing_client = await db.scalar(
        select(Client).where(Client.business_id == business.id, Client.user_id == user.id)
    )
    if not existing_client:
        db.add(Client(business_id=business.id, user_id=user.id, name=user.first_name))
    await db.commit()

    return JoinBusinessOut(
        business_id=business.id,
        business_name=business.name,
        role="client",
    )
