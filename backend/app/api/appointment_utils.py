from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Appointment, Client
from app.schemas.appointment import AppointmentOut


def appointment_query():
    return select(Appointment).options(
        joinedload(Appointment.barber),
        joinedload(Appointment.client).joinedload(Client.user),
        joinedload(Appointment.service),
    )


def to_out(item: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=item.id,
        barber_id=item.barber_member_id,
        client_id=item.client_id,
        service_id=item.service_id,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        status=item.status,
        price_minor=item.price_minor,
        duration_minutes=item.duration_minutes,
        cancelled_at=item.cancelled_at,
        barber_name=item.barber.display_name if item.barber else None,
        client_name=item.client.name if item.client else None,
        service_name=item.service.name if item.service else None,
    )
