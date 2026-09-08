from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.appointment_utils import appointment_query, to_out
from app.api.deps import get_current_user, get_membership, require_staff
from app.core.database import get_db
from app.core.timeutils import as_utc
from app.models import Appointment, Business, BusinessMember, Client, ScheduleBlock, Service, User, WorkingInterval
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.workers.celery_app import celery_app, schedule_booking_reminder

router = APIRouter(prefix="/appointments", tags=["appointments"])
ACTIVE_STATUSES = ("pending", "confirmed")


async def client_for_user(user: User, business_id: int, db: AsyncSession) -> Client:
    item = await db.scalar(select(Client).where(Client.business_id == business_id, Client.user_id == user.id))
    if item:
        return item
    item = Client(business_id=business_id, user_id=user.id, name=user.first_name)
    db.add(item)
    await db.flush()
    return item


async def ensure_slot_is_valid(
    db: AsyncSession,
    business: Business,
    barber_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    tz = ZoneInfo(business.timezone)
    local_start = starts_at.astimezone(tz)
    local_end = ends_at.astimezone(tz)
    if local_start.date() != local_end.date():
        raise HTTPException(status_code=422, detail="An appointment cannot cross midnight")

    intervals = list((await db.execute(
        select(WorkingInterval).where(
            WorkingInterval.barber_member_id == barber_id,
            WorkingInterval.weekday == local_start.weekday(),
        )
    )).scalars().all())
    fits_working_hours = any(
        local_start.time() >= interval.start_time and local_end.time() <= interval.end_time
        for interval in intervals
    )
    if not fits_working_hours:
        raise HTTPException(status_code=422, detail="Appointment is outside the barber's working hours")

    overlap_block = await db.scalar(select(ScheduleBlock.id).where(
        ScheduleBlock.barber_member_id == barber_id,
        ScheduleBlock.starts_at < ends_at,
        ScheduleBlock.ends_at > starts_at,
    ))
    if overlap_block:
        raise HTTPException(status_code=409, detail="This time is blocked")


def reminder_text(item: Appointment, business: Business) -> str:
    local = item.starts_at.astimezone(ZoneInfo(business.timezone))
    service_name = item.service.name if item.service else "запись"
    return f"Напоминание: {service_name}, {local.strftime('%d.%m.%Y')} в {local.strftime('%H:%M')}."


def schedule_reminder_for_item(item: Appointment, business: Business) -> None:
    telegram_id = item.client.user.telegram_id if item.client and item.client.user else None
    task_id = schedule_booking_reminder(item.id, item.starts_at, telegram_id, reminder_text(item, business))
    item.reminder_task_id = task_id


def revoke_reminder(item: Appointment) -> None:
    if item.reminder_task_id:
        try:
            celery_app.control.revoke(item.reminder_task_id, terminate=False)
        except Exception:
            pass
        item.reminder_task_id = None


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    target_date: date | None = Query(default=None, alias="date"),
    status: str | None = Query(default=None),
    barber_id: int | None = Query(default=None),
    user: User = Depends(get_current_user),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[AppointmentOut]:
    query = appointment_query().where(Appointment.business_id == membership.business_id)
    if membership.role == "barber":
        query = query.where(Appointment.barber_member_id == membership.id)
    elif membership.role == "client":
        client = await db.scalar(select(Client).where(Client.business_id == membership.business_id, Client.user_id == user.id))
        if not client:
            return []
        query = query.where(Appointment.client_id == client.id)
    elif barber_id:
        query = query.where(Appointment.barber_member_id == barber_id)

    if status:
        if status not in {"pending", "confirmed", "completed", "cancelled", "no_show"}:
            raise HTTPException(status_code=422, detail="Invalid appointment status")
        query = query.where(Appointment.status == status)

    result = await db.execute(query.order_by(Appointment.starts_at))
    items = list(result.unique().scalars().all())
    if target_date:
        business = await db.get(Business, membership.business_id)
        day_start = as_utc(datetime.combine(target_date, time.min), business.timezone)
        day_end = day_start + timedelta(days=1)
        items = [x for x in items if x.starts_at < day_end and x.ends_at > day_start]
    return [to_out(item) for item in items]


@router.get("/mine", response_model=list[AppointmentOut])
async def my_appointments(
    user: User = Depends(get_current_user),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[AppointmentOut]:
    client = await db.scalar(select(Client).where(Client.business_id == membership.business_id, Client.user_id == user.id))
    if not client:
        return []
    result = await db.execute(appointment_query().where(Appointment.client_id == client.id).order_by(Appointment.starts_at.desc()))
    return [to_out(item) for item in result.unique().scalars().all()]


@router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    payload: AppointmentCreate,
    user: User = Depends(get_current_user),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> AppointmentOut:
    barber = await db.get(BusinessMember, payload.barber_id)
    service = await db.get(Service, payload.service_id)
    business = await db.get(Business, membership.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not barber or barber.business_id != membership.business_id or barber.role not in {"owner", "barber"} or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barber not found")
    if not service or service.business_id != membership.business_id or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")

    starts_at = as_utc(payload.starts_at, business.timezone)
    if starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Appointment must be in the future")
    ends_at = starts_at + timedelta(minutes=service.duration_minutes)
    await ensure_slot_is_valid(db, business, barber.id, starts_at, ends_at)

    if membership.role == "client":
        if payload.client_id is not None or payload.client_name is not None:
            raise HTTPException(status_code=403, detail="Clients cannot choose another client")
        client = await client_for_user(user, membership.business_id, db)
    else:
        require_staff(membership)
        if membership.role == "barber" and barber.id != membership.id:
            raise HTTPException(status_code=403, detail="A barber can create appointments only for themselves")
        if payload.client_id is not None:
            client = await db.get(Client, payload.client_id)
            if not client or client.business_id != membership.business_id:
                raise HTTPException(status_code=404, detail="Client not found")
        else:
            if not payload.client_name:
                raise HTTPException(status_code=422, detail="client_name is required for a manual appointment")
            client = Client(business_id=membership.business_id, name=payload.client_name, phone=payload.client_phone)
            db.add(client)
            await db.flush()

    item = Appointment(
        business_id=membership.business_id,
        barber_member_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        starts_at=starts_at,
        ends_at=ends_at,
        status="confirmed",
        price_minor=service.price_minor,
        duration_minutes=service.duration_minutes,
    )
    db.add(item)
    try:
        await db.flush()
        # Reload relations needed for reminder text before commit.
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This time is already booked") from exc

    item = await db.scalar(appointment_query().where(Appointment.id == item.id))
    assert item is not None
    schedule_reminder_for_item(item, business)
    await db.commit()
    return to_out(item)


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> AppointmentOut:
    item = await db.scalar(appointment_query().where(Appointment.id == appointment_id))
    if not item or item.business_id != membership.business_id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if item.status in {"cancelled", "completed"}:
        raise HTTPException(status_code=409, detail="Appointment cannot be cancelled")

    if membership.role == "client":
        client = await db.scalar(select(Client).where(Client.id == item.client_id, Client.user_id == user.id))
        if not client:
            raise HTTPException(status_code=403, detail="Forbidden")
    elif membership.role == "barber":
        if item.barber_member_id != membership.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    elif membership.role != "owner":
        raise HTTPException(status_code=403, detail="Forbidden")

    revoke_reminder(item)
    item.status = "cancelled"
    item.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    return to_out(item)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    user: User = Depends(get_current_user),
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> AppointmentOut:
    item = await db.scalar(appointment_query().where(Appointment.id == appointment_id))
    if not item or item.business_id != membership.business_id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if membership.role == "barber" and item.barber_member_id != membership.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if membership.role not in {"owner", "barber"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    if item.status == "completed" and (payload.starts_at is not None or payload.status not in {None, "completed"}):
        raise HTTPException(status_code=409, detail="Completed appointment cannot be changed")

    business = await db.get(Business, membership.business_id)
    if payload.starts_at is not None:
        if item.status in {"cancelled", "completed", "no_show"}:
            raise HTTPException(status_code=409, detail="This appointment is no longer reschedulable")
        start = as_utc(payload.starts_at, business.timezone)
        if start <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail="Appointment must be in the future")
        new_end = start + timedelta(minutes=item.duration_minutes)
        await ensure_slot_is_valid(db, business, item.barber_member_id, start, new_end)
        item.starts_at = start
        item.ends_at = new_end
        revoke_reminder(item)
    if payload.status:
        if payload.status == "confirmed" and item.status in {"cancelled", "completed", "no_show"} and payload.starts_at is None:
            raise HTTPException(status_code=422, detail="Restoring an appointment requires a new future time")
        if payload.status == "cancelled":
            revoke_reminder(item)
            item.cancelled_at = datetime.now(timezone.utc)
        elif payload.status in {"completed", "no_show"}:
            revoke_reminder(item)
        elif payload.status == "confirmed":
            item.cancelled_at = None
        item.status = payload.status

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This time is already booked") from exc
    item = await db.scalar(appointment_query().where(Appointment.id == appointment_id))
    assert item is not None
    if item.status in ACTIVE_STATUSES and item.client.user_id and (payload.starts_at is not None or payload.status in ACTIVE_STATUSES):
        schedule_reminder_for_item(item, business)
        await db.commit()
    return to_out(item)
