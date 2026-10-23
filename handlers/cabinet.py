"""Личный кабинет: продукты, рефералы, достижения, задания, заявки."""

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database import (
    get_application,
    get_user_applications,
    get_referral_count,
    get_active_referral_count,
    get_user_profile,
    get_user_achievements,
    get_user_products
)
from loader import bot


router = Router()


@router.callback_query(F.data == "cabinet")
async def cabinet(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = get_user_profile(user_id)

    if not user:
        await callback.answer(
            "Профиль не найден",
            show_alert=True
        )
        return

    balance = user[3] or 0
    points = user[4] or 0
    level = user[5] or "START"
    total_earned = user[6] or 0

    applications = get_user_applications(user_id)
    referrals = get_referral_count(user_id)

    levels = {
        "START": (0, 500, "PRO"),
        "PRO": (500, 1500, "ELITE"),
        "ELITE": (1500, 3000, "MASTER"),
        "MASTER": (3000, 6000, "LEGEND"),
        "LEGEND": (6000, 6000, None)
    }

    current_points, target_points, next_level = levels.get(
        level,
        levels["START"]
    )

    if next_level:

        progress = max(
            0,
            min(
                100,
                int(
                    (points - current_points)
                    / (target_points - current_points)
                    * 100
                )
            )
        )

        filled = int(progress / 10)

        progress_bar = (
                "█" * filled +
                "░" * (10 - filled)
        )

        remaining = max(
            0,
            target_points - points
        )

        progress_text = (
            "🏆 <b>ПРОГРЕСС</b>\n"
            f"Уровень: <b>{level}</b>\n"
            f"⭐ {points:,} / {target_points:,}\n\n"
            f"{progress_bar} <b>{progress}%</b>\n"
            f"До <b>{next_level}</b>: "
            f"<b>{remaining:,} ⭐</b>"
        )

    else:

        progress_text = (
            "🏆 <b>ПРОГРЕСС</b>\n"
            f"Уровень: <b>{level}</b>\n"
            f"⭐ <b>{points:,}</b>\n\n"
            "🔥 <b>МАКСИМАЛЬНЫЙ УРОВЕНЬ</b>"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Мои заявки",
                    callback_data="my_applications"
                ),
                InlineKeyboardButton(
                    text="💸 История выплат",
                    callback_data="withdrawal_history"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Партнёрская программа",
                    callback_data="referral_program"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏅 Достижения",
                    callback_data="achievements"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Задания",
                    callback_data="tasks"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Мои продукты",
                    callback_data="my_products"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Вывести средства",
                    callback_data="withdraw"
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

    text = (
        "👤 <b>ЛИЧНЫЙ КАБИНЕТ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🆔 ID: <code>{user_id}</code>\n\n"

        "💰 <b>ФИНАНСЫ</b>\n"
        f"💳 Баланс: <b>{balance:,} ₽</b>\n"
        f"📈 Заработано: <b>{total_earned:,} ₽</b>\n\n"

        f"{progress_text}\n\n"

        "📊 <b>СТАТИСТИКА</b>\n"
        f"📋 Заявок: <b>{len(applications)}</b>\n"
        f"👥 Рефералов: <b>{referrals}</b>\n\n"

        "<blockquote>"
        "Выполняй предложения, получай вознаграждения "
        "и прокачивай свой уровень."
        "</blockquote>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "my_products")
async def my_products(callback: CallbackQuery):

    user_id = callback.from_user.id

    products = get_user_products(user_id)

    if products:
        text = (
            "💳 <b>МОИ ПРОДУКТЫ</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "BankFlow не будет рекомендовать "
            "тебе продукты, которые уже есть у тебя.\n\n"
        )

        for product in products:
            text += f"✅ {product}\n"

        text += (
            "\n━━━━━━━━━━━━━━━━━━\n"
            "Добавляй только те продукты, "
            "которыми ты уже пользуешься."
        )

    else:
        text = (
            "💳 <b>МОИ ПРОДУКТЫ</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Ты пока не добавил ни одного продукта.\n\n"
            "<blockquote>"
            "Укажи продукты, которые уже есть у тебя, "
            "и BankFlow сможет точнее подбирать "
            "новые предложения."
            "</blockquote>"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить продукт",
                    callback_data="add_product"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← В личный кабинет",
                    callback_data="cabinet"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "referral_program")
async def referral_program(callback: CallbackQuery):

    user_id = callback.from_user.id

    referral_count = get_referral_count(user_id)
    active_referral_count = get_active_referral_count(user_id)

    academy_unlocked = (
            referral_count >= 5
            and active_referral_count >= 3
    )

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=ref_{user_id}"
    )

    # Статус Академии
    if academy_unlocked:
        academy_status = (
            "🔓 <b>АКАДЕМИЯ ОТКРЫТА</b>\n\n"
            "Ты выполнил условия партнёрской программы.\n"
            "Теперь тебе доступна закрытая программа "
            "обучения BankFlow.\n\n"
        )
    else:
        academy_status = (
            "🔒 <b>АКАДЕМИЯ ЗАКРЫТА</b>\n\n"
            "Для доступа необходимо:\n"
            "• пригласить 5 пользователей\n"
            "• получить 3 подтверждённых действия\n\n"
        )

    # Кнопки
    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text="📤 Пригласить друга",
                url=(
                    "https://t.me/share/url?"
                    f"url={referral_link}"
                )
            )
        ]
    ]

    if academy_unlocked:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="🎓 Открыть Академию",
                    callback_data="academy"
                )
            ]
        )

    keyboard_buttons.append(
        [
            InlineKeyboardButton(
                text="← В личный кабинет",
                callback_data="cabinet"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_buttons
    )

    # Сообщение
    await callback.message.edit_text(
        "👥 <b>ПАРТНЁРСКАЯ ПРОГРАММА</b>\n\n"

        "Приглашайте пользователей в BankFlow "
        "и получайте вознаграждение за их "
        "подтверждённые действия.\n\n"

        f"<b>Приглашено:</b> {referral_count}\n\n"

        "🎓 <b>BANKFLOW ACADEMY</b>\n\n"

        f"👤 Приглашено: <b>{referral_count} / 5</b>\n"
        f"✅ Выполнили условия: "
        f"<b>{active_referral_count} / 3</b>\n\n"

        f"{academy_status}"

        "<b>Ваша персональная ссылка</b>\n"
        f"<code>{referral_link}</code>\n\n"

        "<blockquote>"
        "Вознаграждение начисляется только "
        "после подтверждения выполнения условий "
        "приглашённым пользователем."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "achievements")
async def achievements(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = get_user_profile(user_id)

    if not user:
        await callback.answer(
            "Профиль не найден",
            show_alert=True
        )
        return

    points = user[4] or 0
    total_earned = user[6] or 0
    referrals = get_referral_count(user_id)

    earned = get_user_achievements(user_id)

    earned_codes = {
        achievement[0]
        for achievement in earned
    }

    achievements_list = [
        (
            "first_earning",
            "🥇 ПЕРВЫЙ ЗАРАБОТОК",
            "Получи первое вознаграждение",
            100
        ),
        (
            "500_points",
            "⭐ 500 БАЛЛОВ",
            "Набери 500 ⭐",
            150
        ),
        (
            "10k_earned",
            "💰 ПЕРВЫЕ 10 000 ₽",
            "Заработай 10 000 ₽",
            300
        ),
        (
            "5_referrals",
            "👥 5 РЕФЕРАЛОВ",
            "Пригласи 5 пользователей",
            250
        )
    ]

    text = (
        "🏅 <b>МОИ ДОСТИЖЕНИЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Развивайся в BankFlow, выполняй "
        "условия и получай дополнительные ⭐\n\n"
    )

    for code, title, description, reward in achievements_list:

        if code in earned_codes:
            status = "✅ <b>ПОЛУЧЕНО</b>"
        else:
            status = "🔒 <b>НЕ ПОЛУЧЕНО</b>"

        text += (
            f"{title}\n"
            f"<i>{description}</i>\n"
            f"🎁 Награда: <b>+{reward} ⭐</b>\n"
            f"{status}\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>ТВОЯ СТАТИСТИКА</b>\n\n"
        f"⭐ Баллы: <b>{points:,}</b>\n"
        f"💰 Заработано: <b>{total_earned:,} ₽</b>\n"
        f"👥 Рефералов: <b>{referrals}</b>"
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

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "tasks")
async def tasks(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = get_user_profile(user_id)

    if not user:
        await callback.answer(
            "Профиль не найден",
            show_alert=True
        )
        return

    points = user[4] or 0
    total_earned = user[6] or 0
    referrals = get_referral_count(user_id)

    tasks_list = [
        (
            "first_earning",
            "💰 ПОЛУЧИТЬ ПЕРВОЕ ВОЗНАГРАЖДЕНИЕ",
            "Подтверди первое предложение",
            total_earned >= 1,
            100
        ),
        (
            "500_points",
            "⭐ НАБРАТЬ 500 БАЛЛОВ",
            "Дойди до 500 ⭐",
            points >= 500,
            150
        ),
        (
            "10k_earned",
            "💵 ЗАРАБОТАТЬ 10 000 ₽",
            "Заработай 10 000 ₽",
            total_earned >= 10000,
            300
        ),
        (
            "5_referrals",
            "👥 ПРИГЛАСИТЬ 5 РЕФЕРАЛОВ",
            "Пригласи 5 пользователей",
            referrals >= 5,
            250
        )
    ]

    text = (
        "🎯 <b>ЗАДАНИЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выполняй задания и получай "
        "дополнительные ⭐\n\n"
    )

    for code, title, description, completed, reward in tasks_list:

        if completed:
            status = "✅ <b>ВЫПОЛНЕНО</b>"
        else:
            status = "🔒 <b>В ПРОЦЕССЕ</b>"

        text += (
            f"{title}\n"
            f"<i>{description}</i>\n"
            f"🎁 Награда: <b>+{reward} ⭐</b>\n"
            f"{status}\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 Выполняй предложения, "
        "приглашай пользователей и "
        "прокачивай свой уровень."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏅 Достижения",
                    callback_data="achievements"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← В личный кабинет",
                    callback_data="cabinet"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "my_applications")
async def my_applications_callback(
    callback: CallbackQuery
):

    applications = get_user_applications(
        callback.from_user.id
    )

    if not applications:
        await callback.message.edit_text(
            "📋 <b>МОИ ЗАЯВКИ</b>\n\n"
            "У вас пока нет заявок.\n\n"
            "<blockquote>"
            "Выберите подходящее предложение, "
            "чтобы начать зарабатывать."
            "</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="← В личный кабинет",
                            callback_data="cabinet"
                        )
                    ]
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    statuses = {
        "pending": "🟡 На проверке",
        "approved": "🟢 Подтверждено",
        "rejected": "🔴 Отклонено"
    }

    text = (
        "📋 <b>МОИ ЗАЯВКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите заявку:\n"
    )

    buttons = []

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
            f"\n📄 <b>#{application_id}</b> — "
            f"{offer}\n"
            f"{status_text} • "
            f"<b>{reward:,} ₽</b>\n"
        )

        buttons.append([
            InlineKeyboardButton(
                text=f"📄 Заявка #{application_id}",
                callback_data=f"application:{application_id}"
            )
        ])

    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        f"📊 Всего заявок: <b>{len(applications)}</b>"
    )

    buttons.append([
        InlineKeyboardButton(
            text="← В личный кабинет",
            callback_data="cabinet"
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data.startswith("application:"))
async def application_card(callback: CallbackQuery):

    application_id = int(
        callback.data.split(":")[1]
    )

    application = get_application(
        application_id
    )

    if not application:
        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    # Проверяем, что заявка принадлежит пользователю
    if application[1] != callback.from_user.id:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    application_id = application[0]
    offer_name = application[2]
    reward = application[3]
    fio = application[4]
    email = application[5]
    phone = application[6]
    status = application[7]

    statuses = {
        "pending": "🟡 На проверке",
        "approved": "🟢 Подтверждено",
        "rejected": "🔴 Отклонено"
    }

    status_text = statuses.get(
        status,
        status
    )

    text = (
        "📄 <b>КАРТОЧКА ЗАЯВКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Номер: <b>#{application_id}</b>\n"
        f"🏦 Предложение: <b>{offer_name}</b>\n"
        f"💰 Вознаграждение: <b>{reward:,} ₽</b>\n"
        f"📊 Статус: {status_text}\n\n"
        "👤 <b>ДАННЫЕ</b>\n"
        f"ФИО: <b>{fio or '—'}</b>\n"
        f"Email: <b>{email or '—'}</b>\n"
        f"Телефон: <b>{phone or '—'}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
    )

    if status == "pending":
        text += (
            "⏳ Заявка находится на проверке.\n"
            "Ожидайте решения администратора."
        )

    elif status == "approved":
        text += (
            "✅ Заявка подтверждена.\n"
            f"Вам начислено <b>{reward:,} ₽</b>."
        )

    elif status == "rejected":
        text += (
            "❌ Заявка отклонена.\n"
            "Если вы считаете это ошибкой, "
            "обратитесь в поддержку."
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Мои заявки",
                    callback_data="my_applications"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 В личный кабинет",
                    callback_data="cabinet"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "cabinet_apps")
async def cabinet_applications(callback: CallbackQuery):

    applications = get_user_applications(
        callback.from_user.id
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

    if not applications:
        await callback.message.edit_text(
            "📋 <b>МОИ ЗАЯВКИ</b>\n"
            "<i>История ваших оформлений</i>\n\n"

            "<b>Заявок пока нет</b>\n"
            "Выберите предложение, выполните условия "
            "и отправьте его на проверку.\n\n"

            "<blockquote>"
            "После отправки заявки здесь появится "
            "её текущий статус."
            "</blockquote>",

            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await callback.answer()
        return

    status_names = {
        "pending": "🟡 На проверке",
        "approved": "🟢 Подтверждено",
        "rejected": "🔴 Отклонено"
    }

    text = (
        "📋 <b>МОИ ЗАЯВКИ</b>\n"
        f"<i>Всего заявок: {len(applications)}</i>\n\n"
    )

    for application in applications:

        application_id = application[0]
        offer_name = application[1]
        reward = application[2]
        status = application[3]

        status_text = status_names.get(
            status,
            "⚪ Неизвестный статус"
        )

        text += (
            f"<b>{offer_name}</b>\n"
            f"Вознаграждение: <code>{reward:,} ₽</code>\n"
            f"Статус: {status_text}\n"
            f"<i>Заявка #{application_id}</i>\n\n"
        )

    text += (
        "<blockquote>"
        "Вознаграждение поступает на баланс "
        "после подтверждения заявки."
        "</blockquote>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()
