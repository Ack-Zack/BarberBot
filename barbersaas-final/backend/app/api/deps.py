from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import BusinessMember, User


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    user = await db.get(User, decode_access_token(token))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_membership(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BusinessMember:
    membership = await db.scalar(
        select(BusinessMember)
        .where(BusinessMember.user_id == user.id, BusinessMember.is_active.is_(True))
        .order_by(BusinessMember.id)
        .limit(1)
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No active business membership")
    return membership


def require_staff(membership: BusinessMember) -> BusinessMember:
    if membership.role not in {"owner", "barber"}:
        raise HTTPException(status_code=403, detail="Staff access required")
    return membership


def require_owner(membership: BusinessMember) -> BusinessMember:
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return membership
