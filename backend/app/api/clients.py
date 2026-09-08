from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_membership, require_staff
from app.core.database import get_db
from app.models import Appointment, BusinessMember, Client
from app.schemas.appointment import AppointmentOut
from app.schemas.client import ClientCreate, ClientOut
from app.api.appointment_utils import to_out, appointment_query

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
async def list_clients(
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[ClientOut]:
    require_staff(membership)
    result = await db.execute(
        select(Client)
        .where(Client.business_id == membership.business_id)
        .order_by(Client.name)
    )
    clients = list(result.scalars().all())
    output: list[ClientOut] = []
    for client in clients:
        count = await db.scalar(select(func.count(Appointment.id)).where(Appointment.client_id == client.id)) or 0
        last = await db.scalar(select(func.max(Appointment.starts_at)).where(Appointment.client_id == client.id))
        output.append(ClientOut(
            id=client.id,
            user_id=client.user_id,
            name=client.name,
            phone=client.phone,
            notes=client.notes,
            appointments_count=count,
            last_appointment_at=last.isoformat() if last else None,
        ))
    return output


@router.post("", response_model=ClientOut, status_code=201)
async def create_client(
    payload: ClientCreate,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> ClientOut:
    require_staff(membership)
    item = Client(business_id=membership.business_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ClientOut(**payload.model_dump(), id=item.id, user_id=item.user_id)


@router.get("/{client_id}/appointments", response_model=list[AppointmentOut])
async def client_history(
    client_id: int,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[AppointmentOut]:
    require_staff(membership)
    client = await db.get(Client, client_id)
    if not client or client.business_id != membership.business_id:
        raise HTTPException(status_code=404, detail="Client not found")
    result = await db.execute(
        appointment_query()
        .where(Appointment.client_id == client.id)
        .order_by(Appointment.starts_at.desc())
    )
    return [to_out(item) for item in result.unique().scalars().all()]
