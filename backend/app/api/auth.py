from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, validate_telegram_init_data
from app.models import BusinessMember, User
from app.schemas.auth import AuthResponse, TelegramAuthRequest

router = APIRouter(prefix="/auth", tags=["auth"])


async def issue_for_user(user: User) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(user.id))


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(
    payload: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    data = validate_telegram_init_data(payload.init_data)
    try:
        telegram_id = int(data["id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid Telegram user id") from exc

    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=data.get("username"),
            first_name=data.get("first_name", "Telegram user"),
            last_name=data.get("last_name"),
        )
        db.add(user)
    else:
        user.username = data.get("username")
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name")
    await db.commit()
    await db.refresh(user)
    return await issue_for_user(user)


@router.post("/dev", response_model=AuthResponse)
async def dev_auth(
    role: str = Query(default="client"),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    if not settings.allow_dev_auth or settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    telegram_id_by_role = {
        "barber": 900000001,
        "client": 900000002,
        "onboarding": 900000003,
        "visitor": 900000004,
    }
    telegram_id = telegram_id_by_role.get(role, telegram_id_by_role["client"])
    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        raise HTTPException(status_code=500, detail="Development seed is missing")
    return await issue_for_user(user)


@router.get("/me")
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    membership = await db.scalar(
        select(BusinessMember)
        .where(BusinessMember.user_id == user.id, BusinessMember.is_active.is_(True))
        .order_by(BusinessMember.id)
        .limit(1)
    )
    is_owner = bool(membership and membership.role == "owner")
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": membership.role if membership else "client",
        "business_id": membership.business_id if membership else None,
        "member_id": membership.id if membership else None,
        "display_name": membership.display_name if membership else user.first_name,
        "needs_business": membership is None,
        "can_create_business": membership is None or is_owner,
    }
