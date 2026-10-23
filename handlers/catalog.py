"""Каталог офферов, карточка оффера, персональные ссылки, «Выполнил»."""

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
    create_link_request,
    has_pending_link_request,
    get_link_request,
    complete_link_request,
    create_application,
    has_pending_application
)
from loader import bot
from offers import (
    OFFERS,
    CATEGORIES,
    MAGNIT_LINK,
    is_credit_offer,
    ad_label,
    SAFETY_RULE,
    CREDIT_WARNING
)
from states import PersonalLinkForm, AdminLinkForm


router = Router()


@router.callback_query(F.data.startswith("category:"))
async def show_category(callback: CallbackQuery):

    category_id = callback.data.split(":")[1]
    category = CATEGORIES.get(category_id)

    if not category:
        await callback.answer(
            "Категория не найдена",
            show_alert=True
        )
        return

    category_offers = [
        (offer_id, offer)
        for offer_id, offer in OFFERS.items()
        if offer["category"] == category_id
    ]

    buttons = []

    for offer_id, offer in category_offers:
        buttons.append([
            InlineKeyboardButton(
                text=f"{offer['name']}  ·  {offer['reward']:,} ₽",
                callback_data=f"offer:{offer_id}",
                style="success"
            )
        ])

    if category_id == "business":
        buttons.append([
            InlineKeyboardButton(
                text="📖 Как начать",
                callback_data="business_guide"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="← Все направления",
            callback_data="open_offers"
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    if category_offers:

        text = (
            f"{category['icon']} <b>{category['name'].upper()}</b>\n"
            f"<i>Доступно предложений: {len(category_offers)}</i>\n\n"

            "<b>Выберите предложение</b>\n"
            "Откройте карточку продукта, чтобы посмотреть "
            "вознаграждение и условия.\n\n"

            "<blockquote>"
            "Все условия доступны до перехода "
            "к оформлению."
            "</blockquote>"
        )

    else:

        text = (
            f"{category['icon']} <b>{category['name'].upper()}</b>\n\n"

            "<b>Сейчас предложений нет</b>\n"
            "Новые продукты появятся в этом разделе "
            "после добавления.\n\n"

            "<blockquote>"
            "Вы можете выбрать другое направление."
            "</blockquote>"
        )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

def get_link_callback(offer_id, offer):
    """Куда ведёт кнопка «Получить ссылку» для оффера."""
    if offer_id == "vtb_rko":
        return "vtb_call"

    if offer.get("access") == "personal":
        return f"personal:{offer_id}"

    return f"request_link:{offer_id}"


@router.callback_query(F.data.startswith("offer:"))
async def show_offer(callback: CallbackQuery):

    offer_id = callback.data.split(":")[1]
    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    link_callback = get_link_callback(offer_id, offer)

    if is_credit_offer(offer):
        link_callback = f"credit_warning:{offer_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        "🔎 Проверить условия"
                        if offer_id == "vtb_rko"
                        else "🔗 Получить ссылку"
                    ),
                    callback_data=(
                        "vtb_check_ip"
                        if offer_id == "vtb_rko"
                        else link_callback
                    ),
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data=f"category:{offer['category']}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"🟢 <b>{offer['name']}</b>\n"
        f"<i>{offer['type']}</i>\n\n"

        "<b>Вознаграждение</b>\n"
        f"<code>{offer['reward']:,} ₽</code>\n\n"

        "<b>Условия</b>\n"
        f"{offer['condition']}\n\n"

        "<b>Как получить ссылку</b>\n"
        "Нажмите кнопку ниже.\n"
        "Для некоторых предложений потребуется "
        "дополнительная информация для подготовки ссылки.\n\n"

        "<blockquote>"
        "После получения ссылки оформите предложение "
        "и выполните указанные условия."
        "</blockquote>\n\n"

        f"🛡 {SAFETY_RULE}\n\n"

        f"{ad_label(offer)}",

        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()


@router.callback_query(F.data.startswith("credit_warning:"))
async def credit_warning(callback: CallbackQuery):

    offer_id = callback.data.split(":")[1]
    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Понятно, продолжить",
                    callback_data=get_link_callback(offer_id, offer)
                )
            ],
            [
                InlineKeyboardButton(
                    text="← К предложению",
                    callback_data=f"offer:{offer_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"{CREDIT_WARNING}\n\n"
        f"<b>{offer['name']}</b> — {offer['type']}\n\n"
        f"{ad_label(offer)}",
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()

@router.callback_query(F.data.startswith("request_link:"))
async def request_link(callback: CallbackQuery):

    offer_id = callback.data.split(":")[1]
    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    user = callback.from_user

    username = (
        f"@{user.username}"
        if user.username
        else "без username"
    )

    if has_pending_link_request(
        user.id,
        offer_id
    ):
        await callback.answer(
            "Запрос уже отправлен",
            show_alert=True
        )
        return

    request_id = create_link_request(
        user.id,
        offer_id
    )

    if not request_id:
        await callback.answer(
            "Не удалось создать запрос",
            show_alert=True
        )
        return

    user_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← К предложению",
                    callback_data=f"offer:{offer_id}"
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

    await callback.message.edit_text(
        "🔗 <b>ЗАПРОС ССЫЛКИ ОТПРАВЛЕН</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🏦 <b>{offer['name']}</b>\n"
        f"💰 Вознаграждение: "
        f"<b>{offer['reward']:,} ₽</b>\n\n"

        "⏳ Запрос передан администратору.\n\n"

        "<blockquote>"
        "Как только ссылка будет подготовлена, "
        "вы получите её прямо в этом боте."
        "</blockquote>",

        reply_markup=user_keyboard,
        parse_mode="HTML"
    )

    admin_keyboard = InlineKeyboardMarkup(
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

    await bot.send_message(
        ADMIN_ID,

        "🔗 <b>НОВЫЙ ЗАПРОС ССЫЛКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📄 Запрос: <b>#{request_id}</b>\n"
        f"👤 Пользователь: {username}\n"
        f"🆔 ID: <code>{user.id}</code>\n\n"

        f"🏦 Оффер: <b>{offer['name']}</b>\n"
        f"💰 Вознаграждение: "
        f"<b>{offer['reward']:,} ₽</b>\n\n"

        "⏳ <b>Ожидает выдачи ссылки.</b>",

        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

    await callback.answer(
        "Запрос отправлен"
    )

@router.callback_query(F.data.startswith("personal:"))
async def start_personal_link(
    callback: CallbackQuery,
    state: FSMContext
):
    offer_id = callback.data.split(":", 1)[1]

    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    await state.clear()

    await state.update_data(
        offer_id=offer_id
    )

    await state.set_state(
        PersonalLinkForm.fio
    )

    await callback.message.edit_text(
        "🔐 <b>ПЕРСОНАЛЬНАЯ ССЫЛКА</b>\n"
        "<i>Шаг 1 из 3 · ФИО</i>\n\n"

        f"🏦 <b>{offer['name']}</b>\n"
        f"💰 Вознаграждение: <b>{offer['reward']:,} ₽</b>\n\n"

        "<b>Введите ФИО</b>\n"
        "Укажите фамилию, имя и отчество "
        "так, как они указаны в документах.\n\n"

        "<blockquote>"
        "Данные нужны для подготовки "
        "персональной ссылки."
        "</blockquote>",

        parse_mode="HTML"
    )

    await callback.answer()

@router.message(PersonalLinkForm.fio)
async def personal_fio(
    message: Message,
    state: FSMContext
):

    fio = message.text.strip()

    if len(fio) < 5:
        await message.answer(
            "⚠️ <b>Проверьте ФИО</b>\n\n"
            "Введите фамилию, имя и отчество "
            "так, как они указаны в ваших документах.",
            parse_mode="HTML"
        )
        return

    await state.update_data(
        fio=fio
    )

    await state.set_state(
        PersonalLinkForm.email
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="personal_back_fio"
                )
            ]
        ]
    )

    await message.answer(
        "🔐 <b>ПЕРСОНАЛЬНАЯ ССЫЛКА</b>\n"
        "<i>Шаг 2 из 3 · Email</i>\n\n"

        f"ФИО: <b>{fio}</b>\n\n"

        "<b>Введите Email</b>\n"
        "Укажите актуальный адрес электронной почты.\n\n"

        "<blockquote>"
        "Например: name@example.com"
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "personal_back_fio")
async def personal_back_fio(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.set_state(
        PersonalLinkForm.fio
    )

    await callback.message.edit_text(
        "🔐 <b>ПЕРСОНАЛЬНАЯ ССЫЛКА</b>\n"
        "<i>Шаг 1 из 3 · ФИО</i>\n\n"

        "<b>Введите ФИО</b>\n"
        "Укажите фамилию, имя и отчество "
        "так, как они указаны в документах.\n\n"

        "<blockquote>"
        "Например: Иванов Иван Иванович"
        "</blockquote>",

        parse_mode="HTML"
    )

    await callback.answer()

@router.message(PersonalLinkForm.email)
async def personal_email(
    message: Message,
    state: FSMContext
):

    email = message.text.strip()

    if "@" not in email or "." not in email:
        await message.answer(
            "⚠️ <b>Проверьте Email</b>\n\n"
            "Адрес электронной почты указан некорректно. "
            "Введите его ещё раз.\n\n"
            "<blockquote>"
            "Например: name@example.com"
            "</blockquote>",
            parse_mode="HTML"
        )
        return

    await state.update_data(
        email=email
    )

    data = await state.get_data()
    fio = data.get("fio", "")

    await state.set_state(
        PersonalLinkForm.phone
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="personal_back_email"
                )
            ]
        ]
    )

    await message.answer(
        "🔐 <b>ПЕРСОНАЛЬНАЯ ССЫЛКА</b>\n"
        "<i>Шаг 3 из 3 · Телефон</i>\n\n"
        "<b>Введённые данные</b>\n"
        f"ФИО: <b>{fio}</b>\n"
        f"Email: <code>{email}</code>\n\n"
        "<b>Введите номер телефона</b>\n"
        "Укажите актуальный номер телефона.\n\n"
        "<blockquote>"
        "Например: +7 999 123-45-67"
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "personal_back_email")
async def personal_back_email(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()
    fio = data.get("fio", "")

    await state.set_state(
        PersonalLinkForm.email
    )

    await callback.message.edit_text(
        "🔐 <b>ПЕРСОНАЛЬНАЯ ССЫЛКА</b>\n"
        "<i>Шаг 2 из 3 · Email</i>\n\n"
        f"<b>ФИО:</b> {fio}\n\n"
        "<b>Введите Email</b>\n"
        "Укажите актуальный адрес электронной почты.\n\n"
        "<blockquote>"
        "Например: name@example.com"
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer()

@router.message(PersonalLinkForm.phone)
async def personal_phone(
    message: Message,
    state: FSMContext
):

    phone = message.text.strip()

    phone_digits = "".join(
        symbol for symbol in phone
        if symbol.isdigit()
    )

    if len(phone_digits) < 10 or len(phone_digits) > 15:
        await message.answer(
            "⚠️ <b>Проверьте номер телефона</b>\n\n"
            "Введите корректный номер телефона "
            "и попробуйте ещё раз.\n\n"
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

    offer_id = data["offer_id"]
    offer = OFFERS.get(offer_id)

    if not offer:
        await state.clear()

        await message.answer(
            "Предложение не найдено."
        )
        return

    if has_pending_link_request(
            message.from_user.id,
            offer_id
    ):
        await state.clear()

        await message.answer(
            "🟡 <b>ССЫЛКА УЖЕ СОЗДАЁТСЯ</b>\n\n"
            f"<i>{offer['name']}</i>\n\n"
            "Ваш запрос уже передан на обработку.\n\n"
            "<blockquote>"
            "Когда персональная ссылка будет готова, "
            "бот отправит её отдельным сообщением."
            "</blockquote>",
            parse_mode="HTML"
        )
        return

    request_id = create_link_request(
        telegram_id=message.from_user.id,
        offer_id=offer_id,
        fio=data["fio"],
        email=data["email"],
        phone=phone
    )

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← На главную",
                    callback_data="home"
                )
            ]
        ]
    )

    await message.answer(
        "🟢 <b>ЗАПРОС ПРИНЯТ</b>\n"
        f"<i>{offer['name']}</i>\n\n"

        f"<b>Номер запроса:</b> <code>#{request_id}</code>\n\n"

        "<b>Персональная ссылка создаётся</b>\n"
        "Данные успешно переданы для подготовки "
        "индивидуальной ссылки.\n\n"

        "<blockquote>"
        "После создания ссылки бот отправит её "
        "вам отдельным сообщением."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Создать ссылку",
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

    username = message.from_user.username

    username_text = (
        f"@{username}"
        if username
        else "Не указан"
    )

    await bot.send_message(
        ADMIN_ID,

        "🔗 <b>НОВАЯ ПЕРСОНАЛЬНАЯ ССЫЛКА</b>\n\n"

        f"<b>Запрос:</b> <code>#{request_id}</code>\n"
        f"<b>Предложение:</b> {offer['name']}\n"
        f"<b>Вознаграждение:</b> <code>{offer['reward']:,} ₽</code>\n\n"

        "<b>Данные клиента</b>\n"
        f"ФИО: <code>{data['fio']}</code>\n"
        f"Email: <code>{data['email']}</code>\n"
        f"Телефон: <code>{phone}</code>\n\n"

        "<b>Пользователь</b>\n"
        f"Telegram: {username_text}\n"
        f"ID: <code>{message.from_user.id}</code>",

        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("make_link:"))
async def make_personal_link(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    parts = callback.data.split(":")

    if len(parts) != 2:
        await callback.answer(
            "Некорректный запрос",
            show_alert=True
        )
        return

    request_id = int(parts[1])

    link_request = get_link_request(request_id)

    if not link_request:
        await callback.answer(
            "Запрос не найден",
            show_alert=True
        )
        return

    user_id = link_request[1]
    offer_id = link_request[2]
    status = link_request[7]

    if status != "pending":
        await callback.answer(
            "Этот запрос уже обработан",
            show_alert=True
        )
        return

    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    await state.clear()

    await state.update_data(
        link_request_id=request_id
    )

    await state.set_state(
        AdminLinkForm.link
    )

    await callback.message.answer(
        "🔗 <b>ВЫДАЧА ССЫЛКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📄 Запрос: <b>#{request_id}</b>\n"
        f"👤 Пользователь: <code>{user_id}</code>\n"
        f"🏦 Оффер: <b>{offer['name']}</b>\n"
        f"💰 Вознаграждение: <b>{offer['reward']:,} ₽</b>\n\n"

        "<blockquote>"
        "Отправьте готовую партнёрскую ссылку "
        "одним сообщением."
        "</blockquote>",

        parse_mode="HTML"
    )

    await callback.answer()

@router.message(AdminLinkForm.link)
async def admin_personal_link(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    link = message.text.strip()

    if not (
        link.startswith("https://")
        or link.startswith("http://")
    ):
        await message.answer(
            "⚠️ <b>Некорректная ссылка</b>\n\n"
            "Отправьте готовую партнёрскую ссылку "
            "одним сообщением.\n\n"
            "<blockquote>"
            "Ссылка должна начинаться с "
            "https:// или http://"
            "</blockquote>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()

    request_id = data.get("link_request_id")

    if not request_id:
        await state.clear()

        await message.answer(
            "⚠️ <b>Запрос не найден</b>\n\n"
            "Не удалось определить номер запроса.",
            parse_mode="HTML"
        )
        return

    link_request = get_link_request(request_id)

    if not link_request:
        await state.clear()

        await message.answer(
            "⚠️ <b>Запрос не найден в базе</b>",
            parse_mode="HTML"
        )
        return

    user_id = link_request[1]
    offer_id = link_request[2]
    status = link_request[7]

    if status != "pending":
        await state.clear()

        await message.answer(
            "⚠️ <b>Запрос уже обработан</b>\n\n"
            f"Запрос <code>#{request_id}</code> "
            "больше не ожидает выдачи ссылки.",
            parse_mode="HTML"
        )
        return

    offer = OFFERS.get(offer_id)

    if not offer:
        await state.clear()

        await message.answer(
            "⚠️ <b>Предложение не найдено</b>",
            parse_mode="HTML"
        )
        return

    user_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оформить предложение ↗",
                    url=link,
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✓ Я выполнил условия",
                    callback_data=f"done:{offer_id}"
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

    try:

        await bot.send_message(
            user_id,

            "🟢 <b>ССЫЛКА ГОТОВА</b>\n"
            f"<i>{offer['name']}</i>\n\n"

            "<b>Вознаграждение</b>\n"
            f"<code>{offer['reward']:,} ₽</code>\n\n"

            "<b>Что дальше</b>\n"
            "Перейдите по ссылке и оформите "
            "предложение.\n\n"

            "<b>Условия</b>\n"
            f"{offer['condition']}\n\n"

            "<blockquote>"
            "После выполнения условий вернитесь "
            "в бот и нажмите «Я выполнил условия»."
            "</blockquote>\n\n"

            + (
                f"{CREDIT_WARNING}\n\n"
                if is_credit_offer(offer)
                else ""
            )
            + f"🛡 {SAFETY_RULE}\n\n"
            + ad_label(offer, link),

            reply_markup=user_keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as error:

        await message.answer(
            "❌ <b>Не удалось отправить ссылку</b>\n\n"
            f"<code>{error}</code>\n\n"
            "Запрос сохранён. Можно попробовать "
            "отправить ссылку ещё раз.",
            parse_mode="HTML"
        )
        return

    completed = complete_link_request(
        request_id=request_id,
        personal_link=link
    )

    if not completed:

        await state.clear()

        await message.answer(
            "⚠️ <b>Ссылка отправлена пользователю, "
            "но статус запроса не обновился.</b>\n\n"
            f"Проверьте запрос <code>#{request_id}</code>.",
            parse_mode="HTML"
        )
        return

    await state.clear()

    await message.answer(
        "✅ <b>ССЫЛКА ОТПРАВЛЕНА</b>\n\n"
        f"<b>Запрос:</b> <code>#{request_id}</code>\n"
        f"<b>Предложение:</b> {offer['name']}\n"
        f"<b>Пользователь:</b> <code>{user_id}</code>\n\n"
        "<blockquote>"
        "Ссылка отправлена пользователю, "
        "а запрос отмечен как обработанный."
        "</blockquote>",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("done:"))
async def offer_done(callback: CallbackQuery):

    offer_id = callback.data.split(":")[1]
    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    if has_pending_application(
            callback.from_user.id,
            offer["name"]
    ):
        await callback.answer(
            "Вы уже отправляли заявку по этому предложению.",
            show_alert=True
        )
        return

    application_id = create_application(
        telegram_id=callback.from_user.id,
        offer_name=offer["name"],
        reward=offer["reward"],
        fio="",
        email="",
        phone=""
    )

    admin_keyboard = InlineKeyboardMarkup(
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

    username = callback.from_user.username

    username_text = (
        f"@{username}"
        if username
        else "Не указан"
    )

    await bot.send_message(
        ADMIN_ID,
        "📋 <b>НОВАЯ ЗАЯВКА НА ПРОВЕРКУ</b>\n\n"
        f"<b>Заявка:</b> #{application_id}\n"
        f"<b>Предложение:</b> {offer['name']}\n"
        f"<b>Вознаграждение:</b> {offer['reward']:,} ₽\n\n"
        f"Telegram: {username_text}\n"
        f"ID: <code>{callback.from_user.id}</code>\n\n"
        "<blockquote>"
        "Пользователь сообщил о выполнении условий."
        "</blockquote>",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Мои заявки",
                    callback_data="my_applications"
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

    await callback.message.edit_text(
        "🟡 <b>Заявка отправлена на проверку</b>\n\n"
        f"<b>{offer['name']}</b>\n\n"
        "<b>Вознаграждение</b>\n"
        f"<code>{offer['reward']:,} ₽</code>\n\n"
        "<blockquote>"
        "После подтверждения выполнения условий "
        "вознаграждение поступит на ваш баланс."
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer("Заявка отправлена")

@router.callback_query(F.data == "magnit_pay")
async def magnit_pay(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оформить карту ↗",
                    url=MAGNIT_LINK,
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✓ Я выполнил условия",
                    callback_data="magnit_done",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data="debit_cards"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🟢 <b>Магнит Пэй</b>\n"
        "<i>Дебетовая карта</i>\n\n"

        "💰 <b>Вознаграждение</b>\n"
        "<code>1 000 ₽</code>\n\n"

        "📝 <b>Что необходимо сделать</b>\n"
        "Совершить покупку одним чеком от "
        "<b>500 ₽</b> и оплатить её картой Магнит Пэй.\n\n"

        "🔐 <b>Для проверки понадобятся</b>\n"
        "• ФИО\n"
        "• Email\n"
        "• Номер телефона\n\n"

        "<blockquote>"
        "Данные используются для идентификации заявки "
        "и проверки выполнения условий."
        "</blockquote>\n\n"
        f"🛡 {SAFETY_RULE}\n\n"
        f"{ad_label(OFFERS['magnit_pay'], MAGNIT_LINK)}",
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()
