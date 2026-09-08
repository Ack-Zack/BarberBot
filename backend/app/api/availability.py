from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_membership
from app.core.database import get_db
from app.core.timeutils import as_utc
from app.models import Appointment, Business, BusinessMember, ScheduleBlock, Service, WorkingInterval
from app.schemas.appointment import AvailabilityOut

router = APIRouter(tags=["availability"])


@router.get("/availability", response_model=AvailabilityOut)
async def get_availability(
    barber_id: int,
    service_id: int,
    target_date: date = Query(alias="date"),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> AvailabilityOut:
    barber = await db.get(BusinessMember, barber_id)
    service = await db.get(Service, service_id)
    business = await db.get(Business, membership.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not barber or barber.business_id != membership.business_id or not barber.is_active or barber.role not in {"owner", "barber"}:
        raise HTTPException(status_code=404, detail="Barber not found")
    if not service or service.business_id != membership.business_id or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")

    tz = ZoneInfo(business.timezone)
    today_local = datetime.now(tz).date()
    if target_date < today_local:
        return AvailabilityOut(date=str(target_date), timezone=business.timezone, barber_id=barber_id, service_id=service_id, slots=[])
    if target_date > today_local + timedelta(days=90):
        raise HTTPException(status_code=422, detail="Booking is available only 90 days ahead")

    day_start = datetime.combine(target_date, time.min, tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    now_utc = datetime.now(timezone.utc)

    intervals = list((await db.execute(
        select(WorkingInterval)
        .where(
            WorkingInterval.barber_member_id == barber_id,
            WorkingInterval.weekday == target_date.weekday(),
        )
        .order_by(WorkingInterval.start_time)
    )).scalars().all())
    if not intervals:
        return AvailabilityOut(date=str(target_date), timezone=business.timezone, barber_id=barber_id, service_id=service_id, slots=[])

    appointments = list((await db.execute(
        select(Appointment).where(
            Appointment.barber_member_id == barber_id,
            Appointment.status.in_(["pending", "confirmed"]),
            Appointment.starts_at < day_end,
            Appointment.ends_at > day_start,
        )
    )).scalars().all())
    blocks = list((await db.execute(
        select(ScheduleBlock).where(
            ScheduleBlock.barber_member_id == barber_id,
            ScheduleBlock.starts_at < day_end,
            ScheduleBlock.ends_at > day_start,
        )
    )).scalars().all())

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=30)
    slots: list[str] = []
    seen: set[str] = set()

    for interval in intervals:
        cursor = datetime.combine(target_date, interval.start_time, tzinfo=tz)
        boundary = datetime.combine(target_date, interval.end_time, tzinfo=tz)
        while cursor + duration <= boundary:
            end = cursor + duration
            cursor_utc = as_utc(cursor, business.timezone)
            end_utc = as_utc(end, business.timezone)
            if target_date == today_local and cursor_utc <= now_utc:
                cursor += step
                continue
            blocked = (
                any(x.starts_at < end_utc and x.ends_at > cursor_utc for x in appointments)
                or any(x.starts_at < end_utc and x.ends_at > cursor_utc for x in blocks)
            )
            slot = cursor.strftime("%H:%M")
            if not blocked and slot not in seen:
                slots.append(slot)
                seen.add(slot)
            cursor += step

    return AvailabilityOut(
        date=str(target_date),
        timezone=business.timezone,
        barber_id=barber_id,
        service_id=service_id,
        slots=slots,
    )
