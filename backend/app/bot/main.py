import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.core.config import settings


async def start_handler(message: Message) -> None:
    if not message.from_user:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Открыть BarberSaaS",
            web_app=WebAppInfo(url=settings.telegram_webapp_url),
        )
    ]])
    await message.answer(
        "BarberSaaS — запись к вашему барберу и управление расписанием.",
        reply_markup=keyboard,
    )


async def run() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required for bot worker")
    bot = Bot(settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.message.register(start_handler, CommandStart())
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
