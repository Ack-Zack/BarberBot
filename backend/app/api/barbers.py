from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_membership, require_owner, require_staff
from app.core.config import settings
from app.core.database import get_db
from app.models import Business, BusinessMember, Invitation, User
from app.schemas.barber import BarberInviteCreate, BarberInviteOut, BarberOut

router = APIRouter(prefix="/barbers", tags=["barbers"])


def invite_url(token: str) -> str:
    username = settings.telegram_bot_username.strip().lstrip("@")
    if not username:
        raise HTTPException(status_code=503, detail="Telegram bot username is not configured")
    return f"https://t.me/{username}?startapp={quote(f'i_{token}', safe='')}"


@router.get("", response_model=list[BarberOut])
async def list_barbers(
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[BusinessMember]:
    require_staff(membership)
    result = await db.execute(
        select(BusinessMember)
        .where(
            BusinessMember.business_id == membership.business_id,
            BusinessMember.role.in_(["owner", "barber"]),
            BusinessMember.is_active.is_(True),
        )
        .order_by(BusinessMember.id)
    )
    return list(result.scalars().all())


@router.post("/invites", response_model=BarberInviteOut, status_code=201)
async def create_barber_invite(
    payload: BarberInviteCreate,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> BarberInviteOut:
    require_owner(membership)
    raw = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)
    db.add(
        Invitation(
            business_id=membership.business_id,
            invited_by_member_id=membership.id,
            token_hash=token_hash,
            role="barber",
            expires_at=expires_at,
        )
    )
    await db.commit()
    return BarberInviteOut(url=invite_url(raw), expires_at=expires_at.isoformat())


@router.post("/invites/join", response_model=BarberOut)
async def join_barber_invite(
    token: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BusinessMember:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invite = await db.scalar(
        select(Invitation).where(
            Invitation.token_hash == token_hash,
            Invitation.role == "barber",
            Invitation.used_at.is_(None),
        )
    )
    if not invite or invite.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation is invalid or expired")

    existing = await db.scalar(
        select(BusinessMember).where(
            BusinessMember.user_id == user.id,
            BusinessMember.is_active.is_(True),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="User already belongs to a business")

    member = BusinessMember(
        business_id=invite.business_id,
        user_id=user.id,
        role="barber",
        display_name=user.first_name,
        is_active=True,
    )
    db.add(member)
    invite.used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(member)
    return member


@router.patch("/{barber_id}", response_model=BarberOut)
async def update_barber(
    barber_id: int,
    display_name: str,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> BusinessMember:
    require_owner(membership)
    barber = await db.get(BusinessMember, barber_id)
    if not barber or barber.business_id != membership.business_id or barber.role not in {"owner", "barber"}:
        raise HTTPException(status_code=404, detail="Barber not found")
    display_name = display_name.strip()
    if not display_name:
        raise HTTPException(status_code=422, detail="Display name is required")
    barber.display_name = display_name[:255]
    await db.commit()
    await db.refresh(barber)
    return barber


@router.delete("/{barber_id}", status_code=204)
async def deactivate_barber(
    barber_id: int,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> None:
    require_owner(membership)
    if barber_id == membership.id:
        raise HTTPException(status_code=400, detail="Owner cannot remove themselves")
    barber = await db.get(BusinessMember, barber_id)
    if not barber or barber.business_id != membership.business_id or barber.role != "barber":
        raise HTTPException(status_code=404, detail="Barber not found")
    barber.is_active = False
    await db.commit()
