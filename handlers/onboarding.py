"""Вход в бот: подтверждение 18+, согласие на обработку ПД, /privacy."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database import (
    get_onboarding_status,
    confirm_age,
    set_pd_consent
)
from privacy import (
    PRIVACY_VERSION,
    PRIVACY_PARTS,
    CONSENT_TEXT
)


router = Router()

# Кнопки, доступные до прохождения входа
ONBOARDING_CALLBACKS = {
    "age_yes",
    "age_no",
    "pd_accept",
    "pd_decline",
    "privacy"
}

# Кто уже прошёл вход: не ходим в базу на каждое нажатие
_passed = set()


def mark_onboarded(telegram_id):
    _passed.add(telegram_id)


def is_onboarded(telegram_id):
    if telegram_id in _passed:
        return True

    age_ok, consent_version = get_onboarding_status(telegram_id)

    if age_ok and consent_version == PRIVACY_VERSION:
        _passed.add(telegram_id)
        return True

    return False


def age_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Мне есть 18 лет",
                    callback_data="age_yes",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Мне нет 18",
                    callback_data="age_no"
                )
            ]
        ]
    )


def consent_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔒 Политика конфиденциальности",
                    callback_data="privacy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Даю согласие",
                    callback_data="pd_accept",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Не согласен",
                    callback_data="pd_decline"
                )
            ]
        ]
    )


AGE_TEXT = (
    "🔞 <b>BANKFLOW — ТОЛЬКО 18+</b>\n\n"

    "Здесь собраны банковские и кредитные продукты. "
    "Оформлять их можно только совершеннолетним.\n\n"

    "<b>Важные правила</b>\n"
    "• Оформляйте продукты только на себя.\n"
    "• Никому не передавайте карту, данные от банка и коды из СМС.\n"
    "• BankFlow никогда не спрашивает пароли, коды из СМС "
    "и данные карт.\n\n"

    "<b>Подтвердите, что вам исполнилось 18 лет.</b>"
)


async def send_onboarding(message: Message, telegram_id):
    """Показывает текущий шаг входа: возраст или согласие."""
    age_ok, _ = get_onboarding_status(telegram_id)

    if not age_ok:
        await message.answer(
            AGE_TEXT,
            reply_markup=age_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        CONSENT_TEXT,
        reply_markup=consent_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "age_yes")
async def age_yes(callback: CallbackQuery):

    confirm_age(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    await callback.message.edit_text(
        CONSENT_TEXT,
        reply_markup=consent_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "age_no")
async def age_no(callback: CallbackQuery):

    await callback.message.edit_text(
        "🔞 <b>BankFlow доступен только с 18 лет</b>\n\n"
        "Банковские и кредитные продукты оформляются "
        "только совершеннолетними.\n\n"
        "<blockquote>"
        "Никому не передавайте свои карты, данные и коды из СМС — "
        "даже за вознаграждение."
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "pd_accept")
async def pd_accept(callback: CallbackQuery):

    user_id = callback.from_user.id

    age_ok, _ = get_onboarding_status(user_id)

    if not age_ok:
        await callback.message.edit_text(
            AGE_TEXT,
            reply_markup=age_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    set_pd_consent(user_id, PRIVACY_VERSION)
    mark_onboarded(user_id)

    await callback.message.edit_text(
        "✅ <b>Готово</b>\n\n"
        "Спасибо. Теперь вам доступны все разделы BankFlow.\n\n"
        "<blockquote>"
        "Политику конфиденциальности можно открыть "
        "в любой момент командой /privacy."
        "</blockquote>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть BankFlow",
                        callback_data="home",
                        style="success"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "pd_decline")
async def pd_decline(callback: CallbackQuery):

    await callback.message.edit_text(
        "📄 <b>Без согласия мы не можем продолжить</b>\n\n"
        "Чтобы вести личный кабинет, оформлять заявки и делать "
        "выплаты, BankFlow нужно обрабатывать ваши данные.\n\n"
        "Если передумаете — нажмите /start.",
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "privacy")
async def privacy_callback(callback: CallbackQuery):

    for part in PRIVACY_PARTS:
        await callback.message.answer(
            part,
            parse_mode="HTML"
        )

    if not is_onboarded(callback.from_user.id):
        await send_onboarding(
            callback.message,
            callback.from_user.id
        )

    await callback.answer()


@router.message(Command("privacy"))
async def privacy_command(message: Message):

    for part in PRIVACY_PARTS:
        await message.answer(
            part,
            parse_mode="HTML"
        )
