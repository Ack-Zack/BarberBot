from datetime import time

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import Business, BusinessMember, Client, Service, User, WorkingInterval


async def seed_development_data() -> None:
    async with AsyncSessionLocal() as db:
        business = await db.scalar(select(Business).where(Business.slug == "demo-barbershop"))

        barber_user = await db.scalar(select(User).where(User.telegram_id == 900000001))
        if not barber_user:
            barber_user = User(telegram_id=900000001, username="demo_barber", first_name="Илья", last_name="Барбер")
            db.add(barber_user)

        client_user = await db.scalar(select(User).where(User.telegram_id == 900000002))
        if not client_user:
            client_user = User(telegram_id=900000002, username="demo_client", first_name="Алексей", last_name="Клиент")
            db.add(client_user)

        onboarding_user = await db.scalar(select(User).where(User.telegram_id == 900000003))
        if not onboarding_user:
            onboarding_user = User(telegram_id=900000003, username="demo_new_owner", first_name="Новый", last_name="Владелец")
            db.add(onboarding_user)

        visitor_user = await db.scalar(select(User).where(User.telegram_id == 900000004))
        if not visitor_user:
            visitor_user = User(telegram_id=900000004, username="demo_visitor", first_name="Новый", last_name="Клиент")
            db.add(visitor_user)

        await db.flush()

        if not business:
            business = Business(name="Black Beard", slug="demo-barbershop", timezone="Europe/Moscow")
            db.add(business)
            await db.flush()

            barber = BusinessMember(
                business_id=business.id,
                user_id=barber_user.id,
                role="owner",
                display_name="Илья",
                is_active=True,
            )
            client_member = BusinessMember(
                business_id=business.id,
                user_id=client_user.id,
                role="client",
                display_name="Алексей",
                is_active=True,
            )
            db.add_all([barber, client_member])
            await db.flush()
            db.add_all(
                [
                    Service(
                        business_id=business.id,
                        name="Мужская стрижка",
                        description="Классическая мужская стрижка",
                        duration_minutes=60,
                        price_minor=150000,
                        currency="RUB",
                        is_active=True,
                    ),
                    Service(
                        business_id=business.id,
                        name="Борода",
                        description="Оформление бороды",
                        duration_minutes=30,
                        price_minor=80000,
                        currency="RUB",
                        is_active=True,
                    ),
                ]
            )
            db.add_all(
                [WorkingInterval(barber_member_id=barber.id, weekday=w, start_time=time(9), end_time=time(18)) for w in range(5)]
            )
            db.add(Client(business_id=business.id, user_id=client_user.id, name="Алексей"))

        await db.commit()
