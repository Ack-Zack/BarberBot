from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_membership, require_staff
from app.core.database import get_db
from app.models import BusinessMember, Service
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
async def list_services(
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> list[Service]:
    query = select(Service).where(Service.business_id == membership.business_id)
    if membership.role == "client":
        query = query.where(Service.is_active.is_(True))
    result = await db.execute(query.order_by(Service.is_active.desc(), Service.id))
    return list(result.scalars().all())


@router.post("", response_model=ServiceOut, status_code=201)
async def create_service(
    payload: ServiceCreate,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> Service:
    require_staff(membership)
    item = Service(business_id=membership.business_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{service_id}", response_model=ServiceOut)
async def update_service(
    service_id: int,
    payload: ServiceUpdate,
    membership: BusinessMember = Depends(get_membership),
    db: AsyncSession = Depends(get_db),
) -> Service:
    require_staff(membership)
    item = await db.get(Service, service_id)
    if not item or item.business_id != membership.business_id:
        raise HTTPException(status_code=404, detail="Service not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip()
        if value is not None or key == "is_active":
            setattr(item, key, value)
    if not item.name:
        raise HTTPException(status_code=422, detail="Service name is required")
    await db.commit()
    await db.refresh(item)
    return item
