from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID
from handlers.onboarding import (
    ONBOARDING_CALLBACKS,
    is_onboarded,
    send_onboarding
)


class OnboardingMiddleware(BaseMiddleware):
    """Не пускает дальше, пока пользователь не подтвердил 18+ и согласие на ПД.

    /start пропускается: он регистрирует пользователя и реферала,
    а сам показывает шаг входа (см. handlers/menu.py).
    """

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")

        if not user or user.id == ADMIN_ID or is_onboarded(user.id):
            return await handler(event, data)

        if isinstance(event, Message):
            text = event.text or ""
            command = text.split(maxsplit=1)[0].split("@")[0] if text else ""

            if command in ("/start", "/privacy"):
                return await handler(event, data)

            await send_onboarding(event, user.id)
            return None

        if isinstance(event, CallbackQuery):
            if event.data in ONBOARDING_CALLBACKS:
                return await handler(event, data)

            await event.answer(
                "Сначала подтвердите возраст и согласие "
                "на обработку данных",
                show_alert=True
            )

            if event.message:
                await send_onboarding(event.message, user.id)

            return None

        return await handler(event, data)
