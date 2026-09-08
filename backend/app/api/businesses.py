import re
import unicodedata
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.api.deps import get_current_user, get_membership
from app.core.config import settings
from app.core.database import get_db
from app.models import Business, BusinessMember, User
from app.schemas.business import BookingLinkOut, BusinessCreate, BusinessOut, BusinessUpdate

router = APIRouter(prefix="/businesses", tags=["businesses"])


RUSSIAN_TRANSLIT = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
})

def slugify(value: str) -> str:
    value = value.lower().translate(RUSSIAN_TRANSLIT)
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return cleaned[:48] or "business"


def booking_link(slug: str) -> str:
    username = settings.telegram_bot_username.strip().lstrip("@")
    if not username:
        raise HTTPException(status_code=503, detail="Telegram bot username is not configured")
    return f"https://t.me/{username}?startapp={quote(f'b_{slug}', safe='')}"


@router.post("", response_model=BusinessOut, status_code=201)
async def create_business(
    payload: BusinessCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Business:
    try:
        ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown timezone") from exc

    existing_membership = await db.scalar(
        select(BusinessMember).where(BusinessMember.user_id == user.id, BusinessMember.is_active.is_(True))
    )
    if existing_membership:
        raise HTTPException(status_code=409, detail="User already belongs to a business")

    base = slugify(payload.name.strip())
    slug = base
    n = 1
    while await db.scalar(select(Business.id).where(Business.slug == slug)):
        n += 1
        slug = f"{base}-{n}"

    business = Business(name=payload.name.strip(), slug=slug, timezone=payload.timezone)
    db.add(business)
    await db.flush()
    db.add(BusinessMember(
        business_id=business.id,
        user_id=user.id,
        role="owner",
        display_name=user.first_name,
        is_active=True,
    ))
    await db.commit()
    await db.refresh(business)
    return business


@router.get("/me", response_model=BusinessOut)
async def get_my_business(
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> Business:
    business = await db.get(Business, membership.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.patch("/me", response_model=BusinessOut)
async def update_my_business(
    payload: BusinessUpdate,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> Business:
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can edit business settings")
    business = await db.get(Business, membership.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    data = payload.model_dump(exclude_unset=True)
    if "timezone" in data and data["timezone"]:
        try:
            ZoneInfo(data["timezone"])
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(status_code=422, detail="Unknown timezone") from exc
    for key, value in data.items():
        if value is not None:
            setattr(business, key, value.strip() if isinstance(value, str) else value)
    await db.commit()
    await db.refresh(business)
    return business


@router.get("/me/booking-link", response_model=BookingLinkOut)
async def get_booking_link(
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> BookingLinkOut:
    business = await db.get(Business, membership.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return BookingLinkOut(url=booking_link(business.slug))
