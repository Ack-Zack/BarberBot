from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_membership, require_staff
from app.core.database import get_db
from app.core.timeutils import as_utc
from app.models import Appointment, Business, BusinessMember, ScheduleBlock, WorkingInterval
from app.schemas.schedule import ScheduleBlockCreate, ScheduleBlockOut, WorkingHoursIn

router = APIRouter(prefix="/schedule", tags=["schedule"])


async def get_barber_or_404(barber_id: int, membership: BusinessMember, db: AsyncSession) -> BusinessMember:
    barber = await db.get(BusinessMember, barber_id)
    if not barber or barber.business_id != membership.business_id or barber.role not in {"owner", "barber"} or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barber not found")
    return barber


@router.get("/working-hours/{barber_id}")
async def get_working_hours(
    barber_id: int,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    await get_barber_or_404(barber_id, membership, db)
    result = await db.execute(
        select(WorkingInterval)
        .where(WorkingInterval.barber_member_id == barber_id)
        .order_by(WorkingInterval.weekday, WorkingInterval.start_time)
    )
    return [
        {
            "id": x.id,
            "weekday": x.weekday,
            "start_time": x.start_time.strftime("%H:%M"),
            "end_time": x.end_time.strftime("%H:%M"),
        }
        for x in result.scalars().all()
    ]


@router.put("/working-hours/{barber_id}")
async def replace_working_hours(
    barber_id: int,
    payload: WorkingHoursIn,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if membership.role != "owner" and membership.id != barber_id:
        raise HTTPException(status_code=403, detail="Only the owner or the barber can edit this schedule")
    barber = await get_barber_or_404(barber_id, membership, db)

    await db.execute(delete(WorkingInterval).where(WorkingInterval.barber_member_id == barber.id))
    db.add_all(
        [
            WorkingInterval(
                barber_member_id=barber.id,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
            )
            for item in payload.intervals
        ]
    )
    await db.commit()
    return {"status": "ok", "count": len(payload.intervals)}


@router.get("/blocks", response_model=list[ScheduleBlockOut])
async def list_blocks(
    barber_id: int | None = None,
    target_date: date | None = Query(default=None, alias="date"),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleBlock]:
    require_staff(membership)
    query = select(ScheduleBlock).join(BusinessMember, BusinessMember.id == ScheduleBlock.barber_member_id).where(BusinessMember.business_id == membership.business_id)
    if membership.role == "barber":
        query = query.where(ScheduleBlock.barber_member_id == membership.id)
    elif barber_id:
        query = query.where(ScheduleBlock.barber_member_id == barber_id)
    if target_date:
        business = await db.get(Business, membership.business_id)
        try:
            from zoneinfo import ZoneInfo
            zone = ZoneInfo(business.timezone)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Invalid business timezone") from exc
        local_start = datetime.combine(target_date, time.min, tzinfo=zone)
        local_end = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(timezone.utc)
        utc_end = local_end.astimezone(timezone.utc)
        query = query.where(ScheduleBlock.starts_at < utc_end, ScheduleBlock.ends_at > utc_start)
    result = await db.execute(query.order_by(ScheduleBlock.starts_at))
    return list(result.scalars().all())


@router.post("/blocks", response_model=ScheduleBlockOut, status_code=201)
async def create_block(
    payload: ScheduleBlockCreate,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> ScheduleBlock:
    require_staff(membership)
    if membership.role == "barber" and payload.barber_id != membership.id:
        raise HTTPException(status_code=403, detail="A barber can block only their own schedule")
    barber = await get_barber_or_404(payload.barber_id, membership, db)
    business = await db.get(Business, membership.business_id)
    starts_at = as_utc(payload.starts_at, business.timezone)
    ends_at = as_utc(payload.ends_at, business.timezone)

    overlapping = await db.scalar(
        select(ScheduleBlock.id).where(
            ScheduleBlock.barber_member_id == barber.id,
            ScheduleBlock.starts_at < ends_at,
            ScheduleBlock.ends_at > starts_at,
        )
    )
    if overlapping:
        raise HTTPException(status_code=409, detail="Schedule block overlaps another block")

    appointment_overlap = await db.scalar(
        select(Appointment.id).where(
            Appointment.barber_member_id == barber.id,
            Appointment.status.in_(["pending", "confirmed"]),
            Appointment.starts_at < ends_at,
            Appointment.ends_at > starts_at,
        )
    )
    if appointment_overlap:
        raise HTTPException(status_code=409, detail="Schedule block overlaps an appointment")

    item = ScheduleBlock(
        barber_member_id=barber.id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=payload.reason.strip() if payload.reason else None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/blocks/{block_id}", status_code=204)
async def delete_block(
    block_id: int,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> None:
    require_staff(membership)
    item = await db.get(ScheduleBlock, block_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule block not found")
    barber = await db.get(BusinessMember, item.barber_member_id)
    if not barber or barber.business_id != membership.business_id:
        raise HTTPException(status_code=404, detail="Schedule block not found")
    if membership.role == "barber" and item.barber_member_id != membership.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.delete(item)
    await db.commit()
