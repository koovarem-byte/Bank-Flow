"""Вывод средств и обработка выплат админом."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMIN_ID
from database import (
    subtract_balance,
    get_available_balance,
    create_withdrawal,
    get_user_withdrawals,
    get_withdrawal,
    update_withdrawal_status
)
from loader import bot
from states import WithdrawalForm


router = Router()


@router.callback_query(F.data == "withdrawal_history")
async def withdrawal_history(callback: CallbackQuery):

    withdrawals = get_user_withdrawals(
        callback.from_user.id
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Личный кабинет",
                    callback_data="cabinet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 На главную",
                    callback_data="home"
                )
            ]
        ]
    )

    if not withdrawals:
        text = (
            "💸 <b>История выплат</b>\n\n"
            "У вас пока нет заявок на выплату."
        )

    else:
        text = "💸 <b>История выплат</b>\n\n"

        status_names = {
            "pending": "🟡 На обработке",
            "paid": "🟢 Выплачено",
            "rejected": "🔴 Отклонено"
        }

        for withdrawal in withdrawals:
            withdrawal_id = withdrawal[0]
            amount = withdrawal[1]
            bank = withdrawal[3]
            status = withdrawal[4]

            status_text = status_names.get(
                status,
                status
            )

            text += (
                f"<b>Выплата #{withdrawal_id}</b>\n"
                f"Сумма: <b>{amount:,} ₽</b>\n"
                f"Банк: {bank}\n"
                f"Статус: <b>{status_text}</b>\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "withdraw")
async def withdrawal_from_cabinet(
    callback: CallbackQuery,
    state: FSMContext
):
    available = get_available_balance(
        callback.from_user.id
    )

    if available <= 0:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="← Личный кабинет",
                        callback_data="cabinet"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "💸 <b>Вывод средств</b>\n\n"
            "Сейчас у вас нет средств, "
            "доступных для вывода.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await state.set_state(
        WithdrawalForm.amount
    )

    await callback.message.edit_text(
        "💸 <b>ВЫВОД СРЕДСТВ</b>\n"
        "<i>Шаг 1 из 3</i>\n\n"
        f"Доступно: <code>{available:,} ₽</code>\n\n"
        "<b>Введите сумму вывода</b>\n\n"
        "<blockquote>"
        "Например: 1000"
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer()

@router.message(F.text == "💸 Выплата")
async def withdrawal_start(
    message: Message,
    state: FSMContext
):

    available = get_available_balance(
        message.from_user.id
    )

    if available <= 0:
        await message.answer(
            "💸 Вывод средств\n\n"
            "Сейчас у вас нет средств, доступных для вывода."
        )
        return

    await state.set_state(
        WithdrawalForm.amount
    )

    await message.answer(
        "💸 Создание выплаты\n\n"
        f"Доступно: {available:,} ₽\n\n"
        "Введите сумму вывода:"
    )

@router.callback_query(F.data.startswith("reject_withdrawal:"))
async def reject_withdrawal(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    withdrawal_id = int(
        callback.data.split(":")[1]
    )

    withdrawal = get_withdrawal(withdrawal_id)

    if not withdrawal:
        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    if withdrawal[5] != "pending":
        await callback.answer(
            "Заявка уже обработана",
            show_alert=True
        )
        return

    telegram_id = withdrawal[1]
    amount = withdrawal[2]

    update_withdrawal_status(
        withdrawal_id,
        "rejected"
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        f"❌ Выплата #{withdrawal_id} отклонена"
    )

    await bot.send_message(
        telegram_id,
        "❌ <b>Выплата отклонена</b>\n\n"
        f"Сумма: <code>{amount:,} ₽</code>\n\n"
        "<blockquote>"
        "Средства остались на вашем балансе."
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer("Отклонено")

@router.callback_query(F.data == "cabinet_withdraw")
async def cabinet_withdraw(callback: CallbackQuery, state: FSMContext):

    available = get_available_balance(
        callback.from_user.id
    )

    if available <= 0:
        await callback.answer(
            "Сейчас нет средств, доступных для вывода.",
            show_alert=True
        )
        return

    await state.set_state(
        WithdrawalForm.amount
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Личный кабинет",
                    callback_data="cabinet"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "💸 <b>ВЫВОД СРЕДСТВ</b>\n"
        "<i>Создание заявки на выплату</i>\n\n"

        "<b>Доступно к выводу</b>\n"
        f"<code>{available:,} ₽</code>\n\n"

        "<b>Введите сумму выплаты</b>\n"
        "Отправьте сумму одним сообщением без знака ₽.\n\n"

        "<blockquote>"
        "Например: 1000"
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.message(WithdrawalForm.amount)
async def withdrawal_amount(message: Message, state: FSMContext):

    try:
        amount = int(
            message.text
            .replace(" ", "")
            .replace("₽", "")
        )
    except ValueError:
        await message.answer(
            "⚠️ <b>Некорректная сумма</b>\n\n"
            "Введите сумму только цифрами.\n\n"
            "<blockquote>"
            "Например: 1000"
            "</blockquote>",
            parse_mode="HTML"
        )
        return

    available = get_available_balance(
        message.from_user.id
    )

    if amount <= 0:
        await message.answer(
            "⚠️ <b>Некорректная сумма</b>\n\n"
            "Сумма выплаты должна быть больше 0.",
            parse_mode="HTML"
        )
        return

    if amount > available:
        await message.answer(
            "⚠️ <b>Недостаточно средств</b>\n\n"
            f"Вы указали: <code>{amount:,} ₽</code>\n"
            f"Доступно: <code>{available:,} ₽</code>",
            parse_mode="HTML"
        )
        return

    await state.update_data(
        amount=amount
    )

    await state.set_state(
        WithdrawalForm.phone
    )

    await message.answer(
        "💸 <b>ВЫВОД СРЕДСТВ</b>\n"
        "<i>Шаг 2 из 3</i>\n\n"

        f"Сумма выплаты: <code>{amount:,} ₽</code>\n\n"

        "<b>Введите номер телефона</b>\n"
        "Укажите номер, на который необходимо "
        "отправить перевод.\n\n"

        "<blockquote>"
        "Например: +7 999 123-45-67"
        "</blockquote>",

        parse_mode="HTML"
    )

@router.message(WithdrawalForm.phone)
async def withdrawal_phone(message: Message, state: FSMContext):

    phone = message.text.strip()

    if len(phone) < 10:
        await message.answer(
            "⚠️ <b>Проверьте номер телефона</b>\n\n"
            "Номер выглядит слишком коротким. "
            "Введите его ещё раз.\n\n"
            "<blockquote>"
            "Например: +7 999 123-45-67"
            "</blockquote>",
            parse_mode="HTML"
        )
        return

    await state.update_data(
        phone=phone
    )

    data = await state.get_data()
    amount = data.get("amount", 0)

    await state.set_state(
        WithdrawalForm.bank
    )

    await message.answer(
        "💸 <b>ВЫВОД СРЕДСТВ</b>\n"
        "<i>Шаг 3 из 3</i>\n\n"

        f"Сумма: <code>{amount:,} ₽</code>\n"
        f"Телефон: <code>{phone}</code>\n\n"

        "<b>Укажите банк</b>\n"
        "Напишите название банка, на который "
        "необходимо отправить перевод.\n\n"

        "<blockquote>"
        "Например: Сбербанк"
        "</blockquote>",

        parse_mode="HTML"
    )

@router.message(WithdrawalForm.bank)
async def withdrawal_bank(message: Message, state: FSMContext):

    bank = message.text.strip()

    data = await state.get_data()

    amount = data["amount"]
    phone = data["phone"]

    available = get_available_balance(
        message.from_user.id
    )

    if amount > available:
        await state.clear()

        await message.answer(
            "❌ <b>Недостаточно средств</b>\n\n"
            "Доступный баланс изменился. "
            "Создайте заявку на выплату заново.",
            parse_mode="HTML"
        )
        return

    withdrawal_id = create_withdrawal(
        telegram_id=message.from_user.id,
        amount=amount,
        phone=phone,
        bank=bank
    )

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Личный кабинет",
                    callback_data="cabinet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← На главную",
                    callback_data="home"
                )
            ]
        ]
    )

    await message.answer(
        "🟡 <b>ЗАЯВКА НА ВЫПЛАТУ СОЗДАНА</b>\n"
        f"<i>Заявка #{withdrawal_id}</i>\n\n"

        "<b>Сумма выплаты</b>\n"
        f"<code>{amount:,} ₽</code>\n\n"

        "<b>Реквизиты</b>\n"
        f"Банк: <b>{bank}</b>\n"
        f"Телефон: <code>{phone}</code>\n\n"

        "<blockquote>"
        "Средства зарезервированы до обработки заявки. "
        "После выплаты статус будет обновлён."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✓ Выплачено",
                    callback_data=f"paid:{withdrawal_id}",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"reject_withdrawal:{withdrawal_id}",
                    style="danger"
                )
            ]
        ]
    )

    username = message.from_user.username

    username_text = (
        f"@{username}"
        if username
        else "Не указан"
    )

    await bot.send_message(
        ADMIN_ID,
        "💸 <b>НОВАЯ ЗАЯВКА НА ВЫПЛАТУ</b>\n\n"

        f"<b>Заявка:</b> #{withdrawal_id}\n"
        f"<b>Сумма:</b> <code>{amount:,} ₽</code>\n"
        f"<b>Банк:</b> {bank}\n"
        f"<b>Телефон:</b> <code>{phone}</code>\n\n"

        f"<b>Пользователь</b>\n"
        f"Telegram: {username_text}\n"
        f"ID: <code>{message.from_user.id}</code>",

        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("paid:"))
async def paid_withdrawal(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    withdrawal_id = int(
        callback.data.split(":")[1]
    )

    withdrawal = get_withdrawal(withdrawal_id)

    if not withdrawal:
        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    telegram_id = withdrawal[1]
    amount = withdrawal[2]
    status = withdrawal[5]

    if status != "pending":
        await callback.answer(
            "Эта заявка уже обработана",
            show_alert=True
        )
        return

    if not subtract_balance(
        telegram_id,
        amount,
        f"Выплата #{withdrawal_id}"
    ):
        await callback.answer(
            "Недостаточно средств на балансе",
            show_alert=True
        )
        return

    update_withdrawal_status(
        withdrawal_id,
        "paid"
    )

    await bot.send_message(
        telegram_id,
        "✅ <b>ВЫПЛАТА ВЫПОЛНЕНА</b>\n\n"
        f"Сумма: <code>{amount:,} ₽</code>\n\n"
        "<blockquote>"
        "Заявка на выплату обработана."
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.message.edit_text(
        "✅ <b>ВЫПЛАЧЕНО</b>\n\n"
        f"Заявка: <code>#{withdrawal_id}</code>\n"
        f"Сумма: <code>{amount:,} ₽</code>\n"
        f"Пользователь: <code>{telegram_id}</code>",
        parse_mode="HTML"
    )

    await callback.answer(
        "Выплата подтверждена"
    )
