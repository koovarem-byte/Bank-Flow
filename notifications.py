"""Уведомления админу о действиях из Mini App.

Кнопки — те же callback_data, что и в боте (make_link, approve_app, paid, ...),
поэтому дальше админ работает с заявкой как обычно.
Всё, что ввёл пользователь, экранируется (parse_mode=HTML).
"""

from html import escape

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID
from loader import bot


SOURCE = "<i>Источник: Mini App</i>"


def _user_lines(user):
    username = user.get("username")
    username_text = f"@{escape(username)}" if username else "Не указан"

    return (
        "<b>Пользователь</b>\n"
        f"Telegram: {username_text}\n"
        f"ID: <code>{user['id']}</code>"
    )


async def notify_link_request(request_id, offer, user, fio=None, email=None, phone=None):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Выдать ссылку",
                    callback_data=f"make_link:{request_id}",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Написать комментарий",
                    callback_data=f"comment_link:{request_id}"
                )
            ]
        ]
    )

    client = ""

    if fio or email or phone:
        client = (
            "<b>Данные клиента</b>\n"
            f"ФИО: <code>{escape(fio or '')}</code>\n"
            f"Email: <code>{escape(email or '')}</code>\n"
            f"Телефон: <code>{escape(phone or '')}</code>\n\n"
        )

    await bot.send_message(
        ADMIN_ID,
        "🔗 <b>НОВЫЙ ЗАПРОС ССЫЛКИ</b>\n\n"
        f"<b>Запрос:</b> <code>#{request_id}</code>\n"
        f"<b>Предложение:</b> {escape(offer['name'])}\n"
        f"<b>Вознаграждение:</b> <code>{offer['reward']:,} ₽</code>\n\n"
        f"{client}"
        f"{_user_lines(user)}\n\n"
        f"{SOURCE}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def notify_application(application_id, offer_id, offer, user, link_issued_at):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить",
                    callback_data=f"approve_app:{application_id}",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"reject_app:{application_id}",
                    style="danger"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Написать комментарий",
                    callback_data=f"comment_app:{application_id}"
                )
            ]
        ]
    )

    link_issued_text = (
        link_issued_at.strftime("%d.%m.%Y %H:%M")
        if link_issued_at
        else "не выдавалась через бот"
    )

    await bot.send_message(
        ADMIN_ID,
        "📋 <b>НОВАЯ ЗАЯВКА НА ПРОВЕРКУ</b>\n\n"
        f"<b>Заявка:</b> #{application_id}\n"
        f"<b>Предложение:</b> {escape(offer['name'])} "
        f"(<code>{offer_id}</code>)\n"
        f"<b>Вознаграждение:</b> {offer['reward']:,} ₽\n\n"
        f"{_user_lines(user)}\n"
        f"subid для сверки в сети: <code>{user['id']}</code>\n\n"
        f"<b>Ссылка выдана:</b> {link_issued_text}\n\n"
        "<blockquote>"
        "Пользователь сообщил о выполнении условий."
        "</blockquote>\n"
        f"{SOURCE}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def notify_withdrawal(withdrawal_id, amount, phone, bank, user):
    keyboard = InlineKeyboardMarkup(
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

    await bot.send_message(
        ADMIN_ID,
        "💸 <b>НОВАЯ ЗАЯВКА НА ВЫПЛАТУ</b>\n\n"
        f"<b>Заявка:</b> #{withdrawal_id}\n"
        f"<b>Сумма:</b> <code>{amount:,} ₽</code>\n"
        f"<b>Банк:</b> {escape(bank)}\n"
        f"<b>Телефон:</b> <code>{escape(phone)}</code>\n\n"
        f"{_user_lines(user)}\n\n"
        f"{SOURCE}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
