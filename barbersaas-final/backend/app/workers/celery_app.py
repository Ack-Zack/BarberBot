from datetime import datetime, timezone

import httpx
from celery import Celery

from app.core.config import settings

celery_app = Celery("barbersaas", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="barbersaas.send_booking_reminder")
def send_booking_reminder(appointment_id: int, telegram_id: int, text: str) -> None:
    if not settings.telegram_bot_token or not telegram_id:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    with httpx.Client(timeout=10) as client:
        response = client.post(url, json={"chat_id": telegram_id, "text": text})
        response.raise_for_status()


def schedule_booking_reminder(appointment_id: int, starts_at: datetime, telegram_id: int | None, text: str):
    if not telegram_id:
        return None
    delay_seconds = int((starts_at.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds())
    delay_seconds -= settings.reminder_minutes_before * 60
    if delay_seconds <= 0:
        return None
    try:
        result = send_booking_reminder.apply_async(
            args=[appointment_id, telegram_id, text],
            countdown=delay_seconds,
        )
        return result.id
    except Exception:
        return None
