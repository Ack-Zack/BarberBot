from fastapi import APIRouter
from app.api import appointments, auth, availability, barbers, businesses, clients, onboarding, schedule, services

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(businesses.router)
api_router.include_router(onboarding.join_router)
api_router.include_router(onboarding.router)
api_router.include_router(barbers.router)
api_router.include_router(services.router)
api_router.include_router(clients.router)
api_router.include_router(availability.router)
api_router.include_router(appointments.router)
api_router.include_router(schedule.router)
