import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

import jwt
from fastapi import HTTPException, status

from app.core.config import settings

ALGORITHM = "HS256"


def validate_telegram_init_data(init_data: str) -> dict:
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=500, detail="Telegram bot token is not configured")

    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram hash is missing")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")

    try:
        auth_date = int(values.get("auth_date", "0"))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Telegram auth_date") from exc
    now = int(time.time())
    if not auth_date or auth_date > now + 60 or now - auth_date > settings.telegram_init_data_ttl_seconds:
        raise HTTPException(status_code=401, detail="Telegram initData expired")

    raw_user = values.get("user")
    if not raw_user:
        raise HTTPException(status_code=401, detail="Telegram user missing")
    try:
        return json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=401, detail="Invalid Telegram user payload") from exc


def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": exp},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from exc
