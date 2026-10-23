"""Обработчики старой reply-клавиатуры (её убирает /start). Кандидаты на удаление."""

from aiogram import F, Router
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import SUPPORT_USERNAME
from database import (
    get_balance,
    get_user_applications,
    get_available_balance
)


router = Router()


@router.message(F.text == "💰 Баланс")
async def balance(message: Message):

    balance_value = get_balance(
        message.from_user.id
    )

    available = get_available_balance(
        message.from_user.id
    )

    reserved = balance_value - available

    await message.answer(
        "💰 Ваш баланс\n\n"
        f"Всего: {balance_value:,} ₽\n"
        f"Доступно к выводу: {available:,} ₽\n"
        f"В заявках на выплату: {reserved:,} ₽"
    )

@router.message(F.text == "📋 Мои заявки")
async def my_applications(message: Message):

    applications = get_user_applications(
        message.from_user.id
    )

    if not applications:
        await message.answer(
            "📋 <b>МОИ ЗАЯВКИ</b>\n\n"
            "У вас пока нет заявок.\n\n"
            "<blockquote>"
            "Выберите подходящее предложение, "
            "чтобы начать зарабатывать."
            "</blockquote>",
            parse_mode="HTML"
        )
        return

    statuses = {
        "pending": "🟡 На проверке",
        "approved": "🟢 Подтверждено",
        "rejected": "🔴 Отклонено"
    }

    text = (
        "📋 <b>МОИ ЗАЯВКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for application in applications:

        application_id = application[0]
        offer = application[1]
        reward = application[2]
        status = application[3]

        status_text = statuses.get(
            status,
            status
        )

        text += (
            f"📄 <b>Заявка #{application_id}</b>\n"
            f"🏦 {offer}\n"
            f"💰 Вознаграждение: <b>{reward:,} ₽</b>\n"
            f"Статус: {status_text}\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        f"📊 Всего заявок: <b>{len(applications)}</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← В личный кабинет",
                    callback_data="cabinet"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.message(F.text == "👨‍💻 Поддержка")
async def support(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в поддержку",
                    url=f"https://t.me/{SUPPORT_USERNAME}"
                )
            ]
        ]
    )

    await message.answer(
        "👨‍💻 Поддержка\n\n"
        "Если возник вопрос по оформлению, "
        "проверке заявки или выплате — напишите нам.",
        reply_markup=keyboard
    )

@router.message(F.text == "ℹ️ Как это работает")
async def how_it_works(message: Message):

    await message.answer(
        "ℹ️ Как это работает\n\n"
        "1. Выберите предложение\n"
        "2. Ознакомьтесь с условиями\n"
        "3. Оформите продукт по ссылке\n"
        "4. Выполните условия\n"
        "5. Отправьте заявку на проверку\n"
        "6. Получите вознаграждение на баланс\n"
        "7. Создайте заявку на выплату по СБП"
    )
