import asyncio

from aiohttp import web

from aiogram.filters import Command

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)

from database import (
    create_tables,
    create_link_request,
    add_user,
    has_pending_link_request,
    get_balance,
    get_user_withdrawals,
    get_available_balance,
    get_user_applications,
    has_pending_application,
    create_application,
    get_application,
    update_application_status,
    add_balance,
    get_link_request,
    complete_link_request,
    create_withdrawal,
    get_withdrawal,
    update_withdrawal_status,
    subtract_balance,
    get_users_count,
    get_all_users,
    get_user_profile,
    add_points,
    add_total_earned,
    set_user_level,
    get_admin_stats,
    get_user_growth_stats,
    add_referral,
    get_referral_count,
    get_referrer,
    add_referral_reward,
    get_active_referral_count,
    add_achievement,
    get_user_achievements,
    get_user_products,
    get_milestone_100,
    set_milestone_100,
    set_application_comment,
    set_link_request_comment
)

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    SUPPORT_USERNAME,
    SUPPORT_URL,
    PORT
)

from offers import OFFERS, CATEGORIES

MAGNIT_LINK = "https://lk.bs-rko.ru/click?q=MzY0Nnxwcm9kdWN0"


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class PersonalLinkForm(StatesGroup):
    fio = State()
    email = State()
    phone = State()

class AdminLinkForm(StatesGroup):
    link = State()

class BusinessQuestionForm(StatesGroup):
    question = State()

class VtbCallForm(StatesGroup):
    time = State()
    phone = State()

class AdminBusinessAnswerForm(StatesGroup):
    answer = State()

class AdminCommentForm(StatesGroup):
    comment = State()

class AdminLinkCommentForm(StatesGroup):
    comment = State()

class WithdrawalForm(StatesGroup):
    amount = State()
    phone = State()
    bank = State()

class AdminUserForm(StatesGroup):
    value = State()

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    users_count = get_users_count()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ]
        ]
    )

    await message.answer(
        "🟢 <b>BANKFLOW ADMIN</b>\n\n"
        "<b>Пользователи</b>\n"
        f"👥 Всего зарегистрировано: <code>{users_count}</code>\n\n"
        "<blockquote>"
        "Панель управления BankFlow"
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def show_admin_users(callback: CallbackQuery, page: int = 0):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    users = get_all_users()

    if not users:
        await callback.answer(
            "Пользователей пока нет",
            show_alert=True
        )
        return

    per_page = 10
    total_users = len(users)
    total_pages = (total_users + per_page - 1) // per_page

    if page < 0:
        page = 0

    if page >= total_pages:
        page = total_pages - 1

    start = page * per_page
    end = start + per_page

    page_users = users[start:end]

    text = (
        "👥 <b>ПОЛЬЗОВАТЕЛИ BANKFLOW</b>\n\n"
        f"Всего зарегистрировано: <code>{total_users}</code>\n"
        f"Страница: <b>{page + 1} / {total_pages}</b>\n\n"
        "Выберите пользователя:\n"
    )

    keyboard_rows = []

    for index, user in enumerate(page_users, start=start + 1):

        telegram_id = user[0]
        username = user[1]
        full_name = user[2]
        balance = user[3] or 0

        if username:
            user_display = f"@{username}"
        elif full_name:
            user_display = full_name
        else:
            user_display = "Без имени"

        # Обрезаем слишком длинное имя,
        # чтобы кнопки выглядели аккуратно
        user_display = user_display[:30]

        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    text=f"👤 {index}. {user_display}",
                    callback_data=f"admin_user:{telegram_id}"
                )
            ]
        )

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="← Назад",
                callback_data=f"admin_users_page:{page - 1}"
            )
        )

    navigation.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data=f"admin_users_page:{page}"
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                text="Вперёд →",
                callback_data=f"admin_users_page:{page + 1}"
            )
        )

    keyboard_rows.append(navigation)

    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"admin_users_page:{page}"
            )
        ]
    )

    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="← Админ-панель",
                callback_data="admin_panel"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    await show_admin_users(callback, page=0)


@dp.callback_query(F.data.startswith("admin_users_page:"))
async def admin_users_page(callback: CallbackQuery):

    page = int(callback.data.split(":")[1])

    await show_admin_users(callback, page=page)

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    stats = get_admin_stats()

    growth = get_user_growth_stats()

    text = (
        "📊 <b>BANKFLOW — СТАТИСТИКА</b>\n\n"

        "👥 <b>Пользователи</b>\n"
        f"За 24 часа: <code>+{growth['today']}</code>\n"
        f"За 7 дней: <code>+{growth['week']}</code>\n"
        f"За 30 дней: <code>+{growth['month']}</code>\n"
        f"Всего: <code>{growth['total']}</code>\n\n"
          
        "📋 <b>Заявки</b>\n"
        f"Всего: <code>{stats['applications_total']}</code>\n"
        f"🟡 На проверке: <code>{stats['applications_pending']}</code>\n"
        f"✅ Подтверждено: <code>{stats['applications_approved']}</code>\n"
        f"❌ Отклонено: <code>{stats['applications_rejected']}</code>\n\n"

        "🔗 <b>Персональные ссылки</b>\n"
        f"Всего: <code>{stats['links_total']}</code>\n"
        f"🟡 Ожидают: <code>{stats['links_pending']}</code>\n\n"

        "💸 <b>Выплаты</b>\n"
        f"Всего заявок: <code>{stats['withdrawals_total']}</code>\n"
        f"🟡 Ожидают: <code>{stats['withdrawals_pending']}</code>\n"
        f"✅ Выплачено: <code>{stats['withdrawals_paid']}</code>\n"
        f"❌ Отклонено: <code>{stats['withdrawals_rejected']}</code>\n\n"

        "💰 <b>Выплачено пользователям</b>\n"
        f"<code>{stats['withdrawals_paid_amount']:,} ₽</code>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Админ-панель",
                    callback_data="admin_panel"
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

@dp.callback_query(F.data.startswith("admin_user:"))
async def admin_user_profile(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[1])
    user = get_user_profile(telegram_id)

    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    user_id = user[0]
    username = user[1]
    full_name = user[2]
    balance = user[3] or 0
    points = user[4] or 0
    level = user[5] or "START"
    total_earned = user[6] or 0

    applications = get_user_applications(user_id)
    referrals = get_referral_count(user_id)

    if username:
        user_name = f"@{username}"
    elif full_name:
        user_name = full_name
    else:
        user_name = "Без имени"

    levels = {
        "START": (0, 500, "PRO"),
        "PRO": (500, 1500, "ELITE"),
        "ELITE": (1500, 3000, "MASTER"),
        "MASTER": (3000, 6000, "LEGEND"),
        "LEGEND": (6000, 6000, None)
    }

    current_points, target_points, next_level = levels.get(
        level, levels["START"]
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
        progress_bar = "█" * filled + "░" * (10 - filled)
        remaining = max(0, target_points - points)

        progress_text = (
            "🏆 <b>ПРОГРЕСС</b>\n"
            f"Уровень: <b>{level}</b>\n"
            f"⭐ {points:,} / {target_points:,}\n\n"
            f"{progress_bar} <b>{progress}%</b>\n\n"
            f"До <b>{next_level}</b>: <b>{remaining:,} ⭐</b>"
        )
    else:
        progress_text = (
            "🏆 <b>ПРОГРЕСС</b>\n"
            f"Уровень: <b>{level}</b>\n"
            f"⭐ <b>{points:,}</b>\n\n"
            "🔥 <b>МАКСИМАЛЬНЫЙ УРОВЕНЬ</b>"
        )

    text = (
        "👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>{user_name}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        "💰 <b>ФИНАНСЫ</b>\n"
        f"💳 Баланс: <b>{balance:,} ₽</b>\n"
        f"📈 Заработано: <b>{total_earned:,} ₽</b>\n\n"
        f"{progress_text}\n\n"
        "📊 <b>СТАТИСТИКА</b>\n"
        f"📋 Заявок: <b>{len(applications)}</b>\n"
        f"👥 Рефералов: <b>{referrals}</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Баллы",
                    callback_data=f"admin_points:{user_id}"
                ),
                InlineKeyboardButton(
                    text="💰 Баланс",
                    callback_data=f"admin_balance:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Уровень",
                    callback_data=f"admin_level:{user_id}"
                ),
                InlineKeyboardButton(
                    text="📈 Заработок",
                    callback_data=f"admin_earned:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← К пользователям",
                    callback_data="admin_users"
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

@dp.callback_query(F.data.startswith("admin_points:"))
async def admin_points_start(callback: CallbackQuery, state: FSMContext):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    await state.update_data(
        admin_user_id=user_id,
        action="points"
    )

    await state.set_state(AdminUserForm.value)

    await callback.message.answer(
        "⭐ <b>Изменение баллов</b>\n\n"
        "Введите количество баллов.\n\n"
        "Например:\n"
        "<code>+500</code> — добавить\n"
        "<code>-200</code> — убрать",
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("admin_balance:"))
async def admin_balance_start(callback: CallbackQuery, state: FSMContext):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    await state.update_data(
        admin_user_id=user_id,
        action="balance"
    )

    await state.set_state(AdminUserForm.value)

    await callback.message.answer(
        "💰 <b>Изменение баланса</b>\n\n"
        "Введите сумму.\n\n"
        "Например:\n"
        "<code>+1000</code> — добавить\n"
        "<code>-500</code> — убрать",
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("admin_level:"))
async def admin_level_start(callback: CallbackQuery, state: FSMContext):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    await state.update_data(
        admin_user_id=user_id,
        action="level"
    )

    await state.set_state(AdminUserForm.value)

    await callback.message.answer(
        "🏆 <b>Изменение уровня</b>\n\n"
        "Введите новый уровень:\n\n"
        "<code>START</code>\n"
        "<code>PRO</code>\n"
        "<code>ELITE</code>",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("admin_earned:"))
async def admin_earned_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    await state.update_data(
        admin_user_id=user_id,
        action="earned"
    )

    await state.set_state(AdminUserForm.value)

    await callback.message.answer(
        "📈 <b>Изменение заработка</b>\n\n"
        "Введите сумму, которую нужно добавить "
        "к общему заработку пользователя.\n\n"
        "Например:\n"
        "<code>+5000</code>\n"
        "<code>+12500</code>",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.message(AdminUserForm.value)
async def admin_user_value(message: Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    user_id = data.get("admin_user_id")
    action = data.get("action")

    value = message.text.strip()

    if action == "level":

        level = value.upper()

        if level not in ("START", "PRO", "ELITE"):
            await message.answer(
                "❌ Неверный уровень.\n\n"
                "Используй: START, PRO или ELITE."
            )
            return

        set_user_level(user_id, level)

        await state.clear()

        await message.answer(
            f"🏆 Уровень пользователя изменён на <b>{level}</b>.",
            parse_mode="HTML"
        )

        return

    try:
        amount = int(value)
    except ValueError:
        await message.answer(
            "❌ Введи число.\n\n"
            "Например: <code>+500</code> или <code>-200</code>",
            parse_mode="HTML"
        )
        return

    if amount == 0:
        await message.answer("❌ Сумма не может быть 0.")
        return

    if action == "earned":

        if amount < 0:
            await message.answer(
                "❌ Здесь можно только добавлять "
                "исторический заработок."
            )
            return

        add_total_earned(user_id, amount)

        await state.clear()

        await message.answer(
            f"📈 К общему заработку добавлено "
            f"<b>+{amount:,} ₽</b>.",
            parse_mode="HTML"
        )

        return

    if action == "points":

        add_points(user_id, amount)

        await state.clear()

        await message.answer(
            f"⭐ Баллы изменены на "
            f"<b>{amount:+}</b>.",
            parse_mode="HTML"
        )

    elif action == "balance":

        if amount > 0:
            add_balance(user_id, amount, "Ручное начисление админом")
            result = f"+{amount:,} ₽"
        else:
            success = subtract_balance(
                user_id,
                abs(amount),
                "Ручное списание админом"
            )

            if not success:
                await message.answer(
                    "❌ Нельзя убрать эту сумму: "
                    "недостаточно средств на балансе."
                )
                return

            result = f"{amount:,} ₽"

        await state.clear()

        await message.answer(
            f"💰 Баланс изменён на <b>{result}</b>.",
            parse_mode="HTML"
        )

@dp.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    users_count = get_users_count()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🟢 <b>BANKFLOW ADMIN</b>\n\n"
        "<b>Пользователи</b>\n"
        f"👥 Всего зарегистрировано: <code>{users_count}</code>\n\n"
        "<blockquote>"
        "Панель управления BankFlow"
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.message(CommandStart())
async def start(message: Message):

    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        ref_code = args[1]

        if ref_code.startswith("ref_"):
            try:
                referrer_id = int(ref_code.replace("ref_", "", 1))

                add_referral(
                    referrer_id,
                    message.from_user.id
                )

            except ValueError:
                pass

    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )
    users = get_all_users()

    if len(users) >= 100 and not get_milestone_100():
        set_milestone_100()

        await bot.send_message(
            ADMIN_ID,
            "🔥 <b>BANKFLOW — 100 ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
            "Поздравляю.\n\n"
            "В боте зарегистрировался сотый пользователь.\n\n"
            f"📊 Всего пользователей: <b>{len(users)}</b>\n\n"
            "Можно публиковать объявление "
            "и запускать следующий этап.",
            parse_mode="HTML"
        )
    remove_message = await message.answer(
        "Обновляем интерфейс...",
        reply_markup=ReplyKeyboardRemove()
    )

    await remove_message.delete()

    balance_value = get_balance(message.from_user.id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть предложения",
                    callback_data="open_offers",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Личный кабинет",
                    callback_data="cabinet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Как это работает",
                    callback_data="how"
                ),
                InlineKeyboardButton(
                    text="Поддержка",
                    url=SUPPORT_URL
                )
            ]
        ]
    )

    await message.answer(
        "🟢 <b>BANKFLOW</b>\n"
        "<i>Финансовые предложения с вознаграждением</i>\n\n"

        "<b>Ваш баланс</b>\n"
        f"<code>{balance_value:,} ₽</code>\n\n"

        "Подберите подходящий финансовый продукт "
        "и ознакомьтесь с условиями до оформления.\n\n"

        "<blockquote>"
        "Вознаграждение начисляется после "
        "подтверждения выполнения условий."
        "</blockquote>\n\n"

        "<b>Выберите действие</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "open_offers")
async def open_offers(callback: CallbackQuery):

    users = get_all_users()
    user_count = len(users)

    buttons = [
        [
            InlineKeyboardButton(
                text="💳 Дебетовые карты",
                callback_data="category:debit"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Кредитные карты",
                callback_data="category:credit"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏢 Для бизнеса",
                callback_data="category:business"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Инвестиции",
                callback_data="category:invest"
            )
        ],
        [
            InlineKeyboardButton(
                text="₽ МФО",
                callback_data="category:mfo"
            )
        ]
    ]

    if user_count >= 100:
        buttons.append([
            InlineKeyboardButton(
                text="🔥 100 пользователей",
                callback_data="milestone_100"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="← На главную",
            callback_data="home"
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(
        "🟢 <b>ПРЕДЛОЖЕНИЯ</b>\n"
        "<i>Выберите финансовый продукт</i>\n\n"

        "В каждом разделе собраны доступные "
        "предложения и условия их оформления.\n\n"

        "<blockquote>"
        "Вознаграждение и необходимые условия "
        "указаны до перехода к оформлению."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "milestone_100")
async def milestone_100(callback: CallbackQuery):

    users = get_all_users()

    if len(users) < 100:
        await callback.answer(
            "Пока ещё не 100 пользователей",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 К предложениям",
                    callback_data="open_offers"
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
        "🔥 <b>BANKFLOW — 100 ПОЛЬЗОВАТЕЛЕЙ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>100 человек уже воспользовались BankFlow.</b>\n\n"

        "Ещё недавно это был просто проект, "
        "а сейчас ботом уже пользуются реальные люди.\n\n"

        "Спасибо каждому, кто тестирует предложения, "
        "находит ошибки и пишет свои замечания.\n\n"

        "<b>Что дальше?</b>\n\n"

        "Добавляем новые предложения, "
        "улучшаем личный кабинет и "
        "делаем работу с заявками удобнее.\n\n"

        "<blockquote>"
        "100 пользователей — первая большая отметка BankFlow."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "cabinet")
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

@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):
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
            f"🏆 <b>{level}</b> → <b>{next_level}</b>\n"
            f"{progress_bar} <b>{progress}%</b>\n"
            f"Осталось: <b>{remaining:,} ⭐</b>"
        )

    else:
        progress_text = (
            "🏆 <b>LEGEND</b>\n"
            "🔥 Максимальный уровень"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть предложения",
                    callback_data="open_offers",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Задания",
                    callback_data="tasks"
                ),
                InlineKeyboardButton(
                    text="👤 Кабинет",
                    callback_data="cabinet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Как это работает",
                    callback_data="how"
                ),
                InlineKeyboardButton(
                    text="Поддержка",
                    url=SUPPORT_URL
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🟢 <b>BankFlow</b>\n"
        "<i>Банковские предложения с вознаграждением</i>\n\n"

        f"Привет, <b>{callback.from_user.first_name}</b>.\n\n"

        "💰 <b>ТВОИ ФИНАНСЫ</b>\n"
        f"Баланс: <b>{balance:,} ₽</b>\n"
        f"Заработано: <b>{total_earned:,} ₽</b>\n\n"

        "🏆 <b>ТВОЙ ПРОГРЕСС</b>\n"
        f"⭐ {points:,} баллов\n"
        f"{progress_text}\n\n"

        "<blockquote>"
        "Выполняй предложения, получай "
        "вознаграждения и прокачивай свой уровень."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "my_products")
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

@dp.callback_query(F.data == "referral_program")
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

@dp.callback_query(F.data == "achievements")
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

@dp.callback_query(F.data == "tasks")
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

@dp.callback_query(F.data == "academy")
async def academy(callback: CallbackQuery):

    user_id = callback.from_user.id

    referral_count = get_referral_count(user_id)
    active_referral_count = get_active_referral_count(user_id)

    if referral_count < 5 or active_referral_count < 3:
        await callback.answer(
            "Академия пока закрыта",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="01 — Как работает BankFlow",
                    callback_data="academy_1"
                )
            ],
            [
                InlineKeyboardButton(
                    text="02 — Как выбирать продукты",
                    callback_data="academy_2"
                )
            ],
            [
                InlineKeyboardButton(
                    text="03 — Как не терять выплаты",
                    callback_data="academy_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text="04 — Как увеличивать доход",
                    callback_data="academy_4"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Партнёрская программа",
                    callback_data="referral_program"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🎓 <b>BANKFLOW ACADEMY</b>\n"
        "<i>Закрытая академия партнёров</i>\n\n"

        "Добро пожаловать.\n\n"

        "Здесь ты узнаешь, как системно "
        "работать с банковскими продуктами, "
        "правильно проходить условия и "
        "использовать BankFlow эффективнее.\n\n"

        "<b>Твоя программа обучения</b>\n\n"

        "01 — Как работает BankFlow\n"
        "02 — Как выбирать продукты\n"
        "03 — Как не терять выплаты\n"
        "04 — Как увеличивать доход\n\n"

        "<blockquote>"
        "Проходи модули последовательно. "
        "Каждый следующий шаг поможет тебе "
        "эффективнее использовать платформу."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "academy_1")
async def academy_1(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← К Академии",
                    callback_data="academy"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🎓 <b>МОДУЛЬ 01</b>\n"
        "<b>КАК РАБОТАЕТ BANKFLOW</b>\n\n"

        "<b>1. Выбираешь продукт</b>\n"
        "В BankFlow собраны банковские продукты "
        "с указанием вознаграждения и условий.\n\n"

        "<b>2. Изучаешь условия</b>\n"
        "Перед оформлением обязательно смотри, "
        "что именно требуется для получения "
        "вознаграждения.\n\n"

        "<b>3. Оформляешь продукт</b>\n"
        "Переходишь по своей ссылке и оформляешь "
        "продукт по условиям конкретного оффера.\n\n"

        "<b>4. Выполняешь условия</b>\n"
        "Например: совершить покупку на определённую "
        "сумму или выполнить другое действие, "
        "указанное в оффере.\n\n"

        "<b>5. Отправляешь заявку</b>\n"
        "После выполнения условий заявка попадает "
        "на проверку.\n\n"

        "<b>6. Получаешь вознаграждение</b>\n"
        "После подтверждения вознаграждение "
        "начисляется на баланс BankFlow.\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "💡 <b>Главное правило</b>\n\n"
        "Не ориентируйся только на размер выплаты.\n"
        "Сначала смотри условия, требования и "
        "срок выполнения — и только потом "
        "оформляй продукт.\n\n"

        "<blockquote>"
        "BankFlow зарабатывает тогда, когда "
        "подтверждается реальное действие. "
        "Поэтому здесь важна не просто регистрация, "
        "а правильное выполнение условий."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "academy_2")
async def academy_2(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← К Академии",
                    callback_data="academy"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🎓 <b>МОДУЛЬ 02</b>\n"
        "<b>КАК ВЫБИРАТЬ ПРОДУКТЫ</b>\n\n"

        "<b>Не всегда самый большой оффер — лучший.</b>\n\n"

        "Перед оформлением смотри на 5 вещей:\n\n"

        "<b>1. Возраст</b>\n"
        "Проверь, подходит ли тебе возрастной "
        "диапазон конкретного продукта.\n\n"

        "<b>2. Регион</b>\n"
        "Некоторые предложения доступны не во всех "
        "регионах. Проверяй условия перед оформлением.\n\n"

        "<b>3. Требования</b>\n"
        "Посмотри, нужны ли ФИО, телефон, email "
        "или другие данные для оформления.\n\n"

        "<b>4. Условие выплаты</b>\n"
        "Главное — понять, какое действие нужно "
        "выполнить для получения вознаграждения.\n\n"

        "<b>5. Сложность</b>\n"
        "Сравнивай не только выплату, но и количество "
        "действий, которые необходимо выполнить.\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "💡 <b>Простой принцип</b>\n\n"

        "Если один продукт даёт 2 000 ₽ за одно "
        "простое действие, а другой — 2 500 ₽, "
        "но требует несколько дополнительных шагов, "
        "первый может оказаться выгоднее по времени "
        "и усилиям.\n\n"

        "<blockquote>"
        "Смотри на оффер целиком: "
        "выплата + условия + требования + "
        "сложность + срок."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "academy_3")
async def academy_3(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← К Академии",
                    callback_data="academy"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🎓 <b>МОДУЛЬ 03</b>\n"
        "<b>КАК НЕ ТЕРЯТЬ ВЫПЛАТЫ</b>\n\n"

        "Большинство проблем возникает не потому, "
        "что продукт плохой, а потому что пользователь "
        "не выполнил одно из условий.\n\n"

        "<b>Перед оформлением:</b>\n\n"

        "☑️ Проверь возраст\n"
        "☑️ Проверь регион\n"
        "☑️ Прочитай условия оффера\n"
        "☑️ Посмотри, какое действие требуется\n"
        "☑️ Проверь срок выполнения условий\n\n"

        "<b>После оформления:</b>\n\n"

        "☑️ Выполни действие именно так, "
        "как указано в условиях\n"
        "☑️ Не пропускай обязательные шаги\n"
        "☑️ Сохрани подтверждение выполнения, "
        "если оно может понадобиться\n"
        "☑️ Следи за статусом заявки в BankFlow\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "⚠️ <b>Главная ошибка</b>\n\n"

        "Не оформляй продукт только потому, "
        "что видишь большую сумму выплаты.\n\n"

        "Сначала условия → потом действие → "
        "потом заявка на подтверждение.\n\n"

        "<blockquote>"
        "Если не уверен, что выполнил условия, "
        "лучше сначала разобраться, а уже потом "
        "отправлять заявку на проверку."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "academy_4")
async def academy_4(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Партнёрская программа",
                    callback_data="referral_program"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← К Академии",
                    callback_data="academy"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🎓 <b>МОДУЛЬ 04</b>\n"
        "<b>КАК УВЕЛИЧИВАТЬ ДОХОД</b>\n\n"

        "BankFlow можно использовать не только "
        "для собственных банковских продуктов.\n\n"

        "<b>1. Используй подходящие офферы</b>\n"
        "Не оформляй всё подряд. Выбирай продукты, "
        "условия которых подходят именно тебе.\n\n"

        "<b>2. Следи за новыми предложениями</b>\n"
        "Условия и доступные продукты могут меняться, "
        "поэтому регулярно проверяй BankFlow.\n\n"

        "<b>3. Используй партнёрскую программу</b>\n"
        "Приглашай людей, которым действительно "
        "могут быть полезны доступные продукты.\n\n"

        "<b>4. Помогай приглашённым</b>\n"
        "Объясняй механику BankFlow и напоминай "
        "внимательно читать условия конкретного "
        "предложения.\n\n"

        "<b>5. Строй систему</b>\n"
        "Твоя задача — не сделать одно действие, "
        "а постепенно разобраться в платформе "
        "и использовать её возможности системно.\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "💡 <b>Главная идея</b>\n\n"

        "Один пользователь может стать партнёром, "
        "а партнёр — источником новых пользователей.\n\n"

        "<b>Пользователь → продукт → результат → "
        "партнёр → новые пользователи</b>\n\n"

        "<blockquote>"
        "Не обещай людям гарантированный доход. "
        "Результат зависит от условий продуктов, "
        "доступности предложений и фактически "
        "выполненных действий."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "withdrawal_history")
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

@dp.callback_query(F.data == "magnit_pay")
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
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "withdraw")
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

@dp.callback_query(F.data == "how")
async def how_callback(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть предложения",
                    callback_data="open_offers",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поддержка",
                    url=SUPPORT_URL
                )
            ],
            [
    InlineKeyboardButton(
        text="О сервисе",
        callback_data="about_service"
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
        "ℹ️ <b>КАК РАБОТАЕТ BANKFLOW</b>\n"
        "<i>От выбора продукта до выплаты</i>\n\n"

        "BankFlow собирает финансовые предложения "
        "партнёров в одном месте. До оформления вы видите "
        "условия продукта и размер вознаграждения.\n\n"

        "<b>Выбор → Оформление → Проверка → Выплата</b>\n\n"

        "<b>Выбор</b>\n"
        "Откройте подходящее предложение и ознакомьтесь "
        "с его условиями.\n\n"

        "<b>Оформление</b>\n"
        "Перейдите по ссылке из BankFlow. Для некоторых "
        "предложений ссылка создаётся персонально.\n\n"

        "<b>Проверка</b>\n"
        "После выполнения условий отправьте заявку. "
        "Она будет проверена перед начислением.\n\n"

        "<b>Выплата</b>\n"
        "После подтверждения вознаграждение появится "
        "в личном кабинете и станет доступно к выводу.\n\n"

        "<blockquote>"
        "Условия отличаются для каждого предложения. "
        "Проверяйте их в карточке продукта до оформления."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "about_service")
async def about_service(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть предложения",
                    callback_data="open_offers",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поддержка",
                    url=SUPPORT_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Как это работает",
                    callback_data="how"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🟢 <b>О СЕРВИСЕ BANKFLOW</b>\n"
        "<i>Финансовые предложения в одном месте</i>\n\n"

        "<b>Что такое BankFlow?</b>\n"
        "Сервис помогает находить финансовые предложения "
        "партнёров, сравнивать условия и получать "
        "предусмотренное вознаграждение после их выполнения.\n\n"

        "<b>Откуда берётся вознаграждение?</b>\n"
        "При оформлении по партнёрской ссылке сервис может "
        "получать вознаграждение от партнёра. Часть выплаты "
        "предусматривается пользователю в соответствии "
        "с условиями конкретного предложения.\n\n"

        "<b>Почему некоторые ссылки персональные?</b>\n"
        "Для отдельных предложений требуется индивидуальная "
        "ссылка. В таком случае бот запросит необходимые "
        "данные для её создания.\n\n"

        "<b>Как проходит подтверждение?</b>\n"
        "После выполнения условий пользователь отправляет "
        "заявку на проверку. После подтверждения "
        "вознаграждение зачисляется на баланс BankFlow.\n\n"

        "<b>Выплата</b>\n"
        "Доступное вознаграждение можно вывести через "
        "личный кабинет, указав данные для перевода.\n\n"

        "<blockquote>"
        "Перед оформлением всегда проверяйте условия "
        "конкретного предложения. Они могут отличаться."
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("category:"))
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

@dp.callback_query(F.data == "business_step:self")
async def business_self_employed(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 ОТКРЫТЬ ГАЙД",
                    callback_data="business_guide_self"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏢 2. РЕГИСТРАЦИЯ БИЗНЕСА",
                    callback_data="business_step:registration",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="business_guide"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🧾 <b>САМОЗАНЯТОСТЬ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>Первый шаг.</b>\n\n"

        "Если ты только начинаешь работать "
        "на себя, сначала разберись "
        "с базовым статусом.\n\n"

        "Здесь ты узнаешь:\n\n"

        "📌 что такое самозанятость\n"
        "📌 кому она подходит\n"
        "📌 как её оформить\n"
        "📌 что делать после регистрации\n\n"

        "<blockquote>"
        "После этого разберём следующий этап — ИП."
        "</blockquote>\n\n"

        "<i>Подробный разбор добавим в гайд.</i>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "business_step:registration")
async def business_registration(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 ПОШАГОВЫЙ ГАЙД",
                    callback_data="business_guide_registration",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏦 ПЕРЕЙТИ К РКО",
                    callback_data="business_step:rko"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 ЗАДАТЬ ВОПРОС",
                    callback_data="business_question"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="business_guide"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏢 <b>РЕГИСТРАЦИЯ БИЗНЕСА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Следующий этап — оформить ИП.</b>\n\n"
        "Это самая прибыльная часть тестирования.\n\n"
        "Но прежде чем переходить к предложениям "
        "РКО, разберёмся с регистрацией бизнеса.\n\n"
        "Здесь ты поймёшь:\n\n"
        "📌 как зарегистрировать ИП\n"
        "📌 что понадобится\n"
        "📌 что делать после регистрации\n"
        "📌 как перейти к РКО\n\n"
        "<blockquote>"
        "Сначала разбираемся с регистрацией.\n"
        "Потом переходим к предложениям."
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "business_guide_registration")
async def business_guide_registration(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1. ЧТО ПОНАДОБИТСЯ",
                    callback_data="registration_step:documents",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="2. КАК ЗАРЕГИСТРИРОВАТЬ",
                    callback_data="registration_step:how"
                )
            ],
            [
                InlineKeyboardButton(
                    text="3. ЧТО ДЕЛАТЬ ПОСЛЕ",
                    callback_data="registration_step:after"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏦 ПЕРЕЙТИ К РКО",
                    callback_data="business_step:rko"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="business_step:registration"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📖 <b>ГАЙД ПО РЕГИСТРАЦИИ ИП</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Разберём регистрацию от начала до конца.</b>\n\n"
        "Сначала подготовишь всё необходимое.\n"
        "Потом подашь заявление.\n"
        "После регистрации разберём переход к РКО.\n\n"
        "<blockquote>"
        "Иди по шагам и не пропускай важные пункты."
        "</blockquote>\n\n"
        "<i>Выбери нужный раздел.</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "registration_step:documents")
async def registration_documents(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="→ КАК ЗАРЕГИСТРИРОВАТЬ",
                    callback_data="registration_step:how",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← К ГАЙДУ",
                    callback_data="business_guide_registration"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📋 <b>ЧТО ПОНАДОБИТСЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Все необходимые данные и документы "
        "разберём на созвоне.\n\n"
        "В BankFlow паспортные данные "
        "не собираем.\n\n"
        "<blockquote>"
        "На созвоне пройдём всё вместе "
        "и разберём твою ситуацию."
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "registration_step:how")
async def registration_how(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📞 ЗАПИСАТЬСЯ НА СОЗВОН",
                    callback_data="business_question",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="→ ЧТО ДЕЛАТЬ ПОСЛЕ",
                    callback_data="registration_step:after"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← К ГАЙДУ",
                    callback_data="business_guide_registration"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏢 <b>КАК ЗАРЕГИСТРИРОВАТЬ ИП</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Пошаговую регистрацию разберём "
        "на созвоне.\n\n"
        "Там же разберём документы, данные "
        "и порядок действий.\n\n"
        "<blockquote>"
        "Всю регистрацию пройдём вместе."
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "registration_step:after")
async def registration_after(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏦 ПЕРЕЙТИ К РКО",
                    callback_data="business_step:rko",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 ЗАПИСАТЬСЯ НА СОЗВОН",
                    callback_data="business_question"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← К ГАЙДУ",
                    callback_data="business_guide_registration"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏦 <b>ЧТО ДЕЛАТЬ ПОСЛЕ РЕГИСТРАЦИИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "После регистрации ИП переходим "
        "к следующему этапу — РКО.\n\n"
        "Здесь уже выбираем предложение "
        "и смотрим условия.\n\n"
        "<blockquote>"
        "ИП → РКО → выполнение условий → вознаграждение"
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "business_question")
async def business_question(callback: CallbackQuery, state: FSMContext):

    await state.clear()
    await state.set_state(BusinessQuestionForm.question)

    await callback.message.edit_text(
        "💬 <b>ЗАДАТЬ ВОПРОС</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "Напиши свой вопрос одним сообщением.\n\n"

        "<blockquote>"
        "Например: «У меня уже есть ИП. "
        "Что делать дальше?»"
        "</blockquote>\n\n"

        "После отправки вопрос попадёт "
        "в поддержку BankFlow.",

        parse_mode="HTML"
    )

    await callback.answer()

@dp.message(BusinessQuestionForm.question)
async def receive_business_question(
    message: Message,
    state: FSMContext
):

    question = message.text

    if not question:
        await message.answer(
            "Напиши вопрос текстом."
        )
        return

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "без username"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Ответить",
                    callback_data=f"answer_business:{message.from_user.id}"
                )
            ]
        ]
    )

    await bot.send_message(
        ADMIN_ID,
        "💬 <b>НОВЫЙ ВОПРОС</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"👤 Пользователь: <b>{message.from_user.full_name}</b>\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"

        "<b>Вопрос:</b>\n"
        f"{question}",

        parse_mode="HTML"
    )

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Вернуться",
                    callback_data="business_step:registration"
                )
            ]
        ]
    )

    await message.answer(
        "✅ <b>ВОПРОС ОТПРАВЛЕН</b>\n\n"
        "Мы получили твой вопрос.\n"
        "Ответ придёт сюда в Telegram.",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("answer_business:"))
async def answer_business_question(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    user_id = int(
        callback.data.split(":")[1]
    )

    await state.clear()

    await state.update_data(
        business_user_id=user_id
    )

    await state.set_state(
        AdminBusinessAnswerForm.answer
    )

    await callback.message.answer(
        "💬 <b>ОТВЕТ ПОЛЬЗОВАТЕЛЮ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Напиши ответ одним сообщением.",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.message(AdminBusinessAnswerForm.answer)
async def receive_business_answer(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    user_id = data.get("business_user_id")

    if not user_id:
        await state.clear()
        await message.answer(
            "Не удалось определить пользователя."
        )
        return

    if not message.text:
        await message.answer(
            "Напиши ответ текстом."
        )
        return

    await bot.send_message(
        user_id,
        "💬 <b>ОТВЕТ ПОДДЕРЖКИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{message.text}",
        parse_mode="HTML"
    )

    await state.clear()

    await message.answer(
        "✅ Ответ отправлен пользователю."
    )

@dp.callback_query(F.data == "business_step:ip")
async def business_ip(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 ОТКРЫТЬ ГАЙД",
                    callback_data="business_guide_ip"
                )
            ],
            [
                InlineKeyboardButton(
                    text="→ 3. РКО",
                    callback_data="business_step:rko",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="business_guide"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏢 <b>ИНДИВИДУАЛЬНЫЙ ПРЕДПРИНИМАТЕЛЬ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>Следующий шаг.</b>\n\n"

        "ИП открывает доступ к предложениям "
        "для предпринимателей, в том числе к РКО.\n\n"

        "Здесь ты узнаешь:\n\n"

        "📌 что такое ИП\n"
        "📌 когда он нужен\n"
        "📌 как его зарегистрировать\n"
        "📌 что делать после регистрации\n\n"

        "<blockquote>"
        "После регистрации можно переходить "
        "к следующему этапу — РКО."
        "</blockquote>\n\n"

        "<i>Подробный разбор добавим в гайд.</i>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "business_step:rko")
async def business_rko(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏦 СМОТРЕТЬ ПРЕДЛОЖЕНИЯ",
                    callback_data="business_offers",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 ОТКРЫТЬ ГАЙД",
                    callback_data="business_guide_rko"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="business_guide"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏦 <b>РКО</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>Ты дошёл до главного этапа.</b>\n\n"

        "РКО помогает предпринимателю "
        "работать с расчётным счётом "
        "и банковскими продуктами для бизнеса.\n\n"

        "В предложениях BankFlow "
        "условия отличаются у каждого банка.\n\n"

        "📌 размер вознаграждения\n"
        "📌 целевое действие\n"
        "📌 требования к клиенту\n"
        "📌 срок выполнения условий\n\n"

        "<blockquote>"
        "Перед оформлением всегда проверь "
        "условия конкретного предложения."
        "</blockquote>\n\n"

        "<i>Выбери предложение, которое "
        "подходит тебе.</i>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "business_full_guide")
async def business_full_guide(callback: CallbackQuery):

    await callback.answer(
        "Полный гайд пока готовится",
        show_alert=True
    )


@dp.callback_query(F.data == "business_guide_self")
async def business_guide_self(callback: CallbackQuery):

    await callback.answer(
        "Гайд по самозанятости пока готовится",
        show_alert=True
    )


@dp.callback_query(F.data == "business_guide_ip")
async def business_guide_ip(callback: CallbackQuery):

    await callback.answer(
        "Гайд по ИП пока готовится",
        show_alert=True
    )


@dp.callback_query(F.data == "business_guide_rko")
async def business_guide_rko(callback: CallbackQuery):

    await callback.answer(
        "Гайд по РКО пока готовится",
        show_alert=True
    )


@dp.callback_query(F.data == "business_offers")
async def business_offers(callback: CallbackQuery):

    category_id = "business"

    category_offers = [
        (offer_id, offer)
        for offer_id, offer in OFFERS.items()
        if offer["category"] == category_id
    ]

    buttons = []

    for offer_id, offer in category_offers:
        buttons.append([
            InlineKeyboardButton(
                text=f"{offer['name']} · {offer['reward']:,} ₽",
                callback_data=f"offer:{offer_id}",
                style="success"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="← Назад",
            callback_data="business_step:rko"
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(
        "🏦 <b>РКО — ПРЕДЛОЖЕНИЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Доступно предложений: "
        f"<b>{len(category_offers)}</b>\n\n"
        "<i>Выбери предложение, чтобы "
        "посмотреть условия.</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "business_guide")
async def business_guide(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧾 1. САМОЗАНЯТОСТЬ",
                    callback_data="business_step:self",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏢 2. ИП",
                    callback_data="business_step:ip",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏦 3. РКО",
                    callback_data="business_step:rko",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 ПОЛНЫЙ ГАЙД",
                    callback_data="business_full_guide"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="category:business"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🔑 <b>РКО — КЛЮЧ К ЗОЛОТУ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "Ты уже прошёл дебетовые "
        "и кредитные карты?\n\n"

        "<b>Тогда пора двигаться дальше.</b>\n\n"

        "🏦 <b>РКО</b>\n\n"

        "В отдельных предложениях "
        "вознаграждение составляет "
        "<b>3 000–6 000 ₽</b>.\n\n"

        "<blockquote>"
        "Сначала разберись с путём.\n"
        "Потом переходи к предложениям."
        "</blockquote>\n\n"

        "🧾 <b>Самозанятость</b>\n"
        "↓\n"
        "🏢 <b>ИП</b>\n"
        "↓\n"
        "🏦 <b>РКО</b>\n\n"

        "<i>Выбери этап и двигайся дальше.</i>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("offer:"))
async def show_offer(callback: CallbackQuery):

    offer_id = callback.data.split(":")[1]
    offer = OFFERS.get(offer_id)

    if not offer:
        await callback.answer(
            "Предложение не найдено",
            show_alert=True
        )
        return

    if offer_id == "vtb_rko":
        link_callback = "vtb_call"

    elif offer.get("access") == "personal":
        link_callback = f"personal:{offer_id}"

    elif offer.get("access") == "manual":
        link_callback = f"request_link:{offer_id}"

    else:
        link_callback = f"request_link:{offer_id}"

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
        "</blockquote>",

        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "vtb_check_ip")
async def vtb_check_ip(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, ИП есть",
                    callback_data="vtb_ip_yes",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, ИП нет",
                    callback_data="vtb_ip_no"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data="offer:vtb_rko"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏦 <b>ВТБ — РКО</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Перед оформлением проверим "
        "одно условие.</b>\n\n"
        "Для этого предложения нужен "
        "зарегистрированный ИП.\n\n"
        "<b>У тебя уже есть ИП?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "vtb_ip_yes")
async def vtb_ip_yes(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await state.set_state(VtbCallForm.time)

    await callback.message.edit_text(
        "🏦 <b>ВТБ — РКО</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Отлично. Тогда можем перейти "
        "к оформлению.\n\n"
        "Я помогу пройти процесс и отвечу "
        "на вопросы.\n\n"
        "⏱ Обычно это занимает 5–10 минут.\n\n"
        "<b>Напиши удобное время для звонка "
        "по МСК.</b>\n\n"
        "<blockquote>"
        "Например: сегодня в 19:30"
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data == "vtb_ip_no")
async def vtb_ip_no(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏢 Регистрация бизнеса",
                    callback_data="business_step:registration",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data="offer:vtb_rko"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🏦 <b>ВТБ — РКО</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Для этого предложения нужен "
        "зарегистрированный ИП.\n\n"
        "Сейчас перейти к оформлению РКО "
        "не получится.\n\n"
        "<blockquote>"
        "Сначала зарегистрируй бизнес, "
        "а после этого возвращайся "
        "к предложениям РКО."
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("request_link:"))
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

@dp.callback_query(F.data == "vtb_call")
async def vtb_call_start(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await state.set_state(
        VtbCallForm.time
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="offer:vtb_rko"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📞 <b>ОФОРМЛЕНИЕ ВТБ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Для этого предложения нужна "
        "персональная заявка.\n\n"
        "⏱ Обычно это занимает 5–10 минут.\n\n"
        "<b>Напиши удобное время для звонка "
        "по МСК.</b>\n\n"
        "<blockquote>"
        "Например: сегодня в 19:30"
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@dp.message(VtbCallForm.time)
async def vtb_call_time(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "Напиши удобное время текстом.\n"
            "Например: сегодня в 19:30"
        )
        return

    await state.update_data(
        call_time=message.text
    )

    await state.set_state(
        VtbCallForm.phone
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="vtb_back_time"
                )
            ]
        ]
    )

    await message.answer(
        "📞 <b>НОМЕР ДЛЯ СВЯЗИ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Теперь отправь номер телефона, "
        "на который удобно позвонить.\n\n"
        "<blockquote>"
        "Номер нужен только для связи по заявке."
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.message(VtbCallForm.phone)
async def vtb_call_phone(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "Отправь номер телефона текстом."
        )
        return

    data = await state.get_data()

    call_time = data.get("call_time")
    phone = message.text.strip()

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "без username"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать пользователю",
                    callback_data=f"vtb_contact:{message.from_user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Обработано",
                    callback_data=f"vtb_done:{message.from_user.id}"
                )
            ]
        ]
    )

    await bot.send_message(
        ADMIN_ID,
        "🏦 <b>НОВАЯ ЗАЯВКА ВТБ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Пользователь: <b>{message.from_user.full_name}</b>\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n\n"
        f"📞 Телефон: <code>{phone}</code>\n"
        f"🕐 Время звонка: <b>{call_time} МСК</b>\n\n"
        "💰 Вознаграждение: <b>3 000 ₽</b>\n"
        "📌 Условие: активация бесплатного счёта",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

    await state.clear()

    await message.answer(
        "✅ <b>ЗАЯВКА ПРИНЯТА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🕐 Время: <b>{call_time} МСК</b>\n"
        f"📞 Телефон: <code>{phone}</code>\n\n"
        "Я свяжусь с тобой в указанное время.",
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "vtb_back_time")
async def vtb_back_time(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()
    await state.set_state(VtbCallForm.time)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← НАЗАД",
                    callback_data="offer:vtb_rko"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📞 <b>ОФОРМЛЕНИЕ ВТБ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Напиши удобное время для звонка "
        "по МСК.</b>\n\n"
        "<blockquote>"
        "Например: сегодня в 19:30"
        "</blockquote>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("vtb_contact:"))
async def vtb_contact(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    user_id = int(
        callback.data.split(":")[1]
    )

    await state.clear()

    await state.update_data(
        business_user_id=user_id
    )

    await state.set_state(
        AdminBusinessAnswerForm.answer
    )

    await callback.message.answer(
        "💬 <b>СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЮ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Напиши сообщение одним текстом.",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("vtb_done:"))
async def vtb_done(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await callback.message.answer(
        "✅ <b>ЗАЯВКА ВТБ ОБРАБОТАНА</b>",
        parse_mode="HTML"
    )

    await callback.answer(
        "Заявка отмечена как обработанная"
    )

@dp.callback_query(F.data.startswith("personal:"))
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

@dp.message(PersonalLinkForm.fio)
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

@dp.callback_query(F.data == "personal_back_fio")
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

@dp.message(PersonalLinkForm.email)
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

@dp.callback_query(F.data == "personal_back_email")
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

@dp.message(PersonalLinkForm.phone)
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

@dp.callback_query(F.data.startswith("make_link:"))
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

@dp.message(AdminLinkForm.link)
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
            "</blockquote>",

            reply_markup=user_keyboard,
            parse_mode="HTML"
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

@dp.message(Command("broadcast100"))
async def broadcast_100(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()

    text = (
        "🔥 <b>BANKFLOW — 100 ПОЛЬЗОВАТЕЛЕЙ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>Нас уже 100.</b>\n\n"

        "Ещё недавно BankFlow был просто идеей, "
        "а сегодня им уже пользуются 100 человек.\n\n"

        "Спасибо каждому, кто тестирует предложения, "
        "находит ошибки и помогает нам делать платформу лучше.\n\n"

        "<b>Что дальше?</b>\n\n"

        "Добавляем новые предложения, "
        "улучшаем личный кабинет и продолжаем развивать BankFlow.\n\n"

        "<blockquote>"
        "100 пользователей — первая большая отметка."
        "</blockquote>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Смотреть предложения",
                    callback_data="open_offers",
                    style="success"
                )
            ]
        ]
    )

    sent = 0
    failed = 0

    for user in users:

        if isinstance(user, (tuple, list)):
            telegram_id = user[0]
        else:
            telegram_id = user

        try:
            await bot.send_message(
                telegram_id,
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            sent += 1

            await asyncio.sleep(0.05)

        except Exception:
            failed += 1

    await message.answer(
        "✅ <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
        f"📨 Отправлено: <b>{sent}</b>\n"
        f"❌ Не доставлено: <b>{failed}</b>",
        parse_mode="HTML"
    )

def check_achievements(telegram_id):

    user = get_user_profile(telegram_id)

    if not user:
        return []

    points = user[4] or 0
    total_earned = user[6] or 0
    referrals = get_referral_count(telegram_id)

    earned_now = []

    checks = [
        (
            "first_earning",
            total_earned >= 1,
            100,
            "🥇 ПЕРВЫЙ ЗАРАБОТОК"
        ),
        (
            "500_points",
            points >= 500,
            150,
            "⭐ 500 БАЛЛОВ"
        ),
        (
            "10k_earned",
            total_earned >= 10000,
            300,
            "💰 ПЕРВЫЕ 10 000 ₽"
        ),
        (
            "5_referrals",
            referrals >= 5,
            250,
            "👥 5 РЕФЕРАЛОВ"
        )
    ]

    for code, condition, reward, title in checks:

        if condition and add_achievement(
            telegram_id,
            code
        ):
            add_points(
                telegram_id,
                reward
            )

            earned_now.append(
                (
                    code,
                    reward,
                    title
                )
            )

    return earned_now

@dp.callback_query(F.data.startswith("approve_app:"))
async def approve_application(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    application_id = int(
        callback.data.split(":")[1]
    )

    application = get_application(application_id)

    if not application:
        await callback.answer("Заявка не найдена")
        return

    if application[7] != "pending":
        await callback.answer(
            "Заявка уже обработана",
            show_alert=True
        )
        return

    telegram_id = application[1]
    offer_name = application[2]
    reward = application[3]

    # Получаем старый уровень
    old_profile = get_user_profile(telegram_id)
    old_level = old_profile[5] if old_profile else "START"

    # Подтверждаем заявку
    update_application_status(
        application_id,
        "approved"
    )

    # Начисляем деньги
    add_balance(
        telegram_id,
        reward,
        f"Заявка #{application_id}: {offer_name}"
    )

    # Начисляем баллы
    add_points(
        telegram_id,
        100
    )

    add_total_earned(
        telegram_id,
        reward
    )

    new_achievements = check_achievements(
        telegram_id
    )
    if new_achievements:

        for achievement in new_achievements:
            achievement_code = achievement[0]
            achievement_reward = achievement[1]
            achievement_title = achievement[2]

            await bot.send_message(
                telegram_id,
                "🏆 <b>НОВОЕ ДОСТИЖЕНИЕ!</b>\n\n"
                f"{achievement_title}\n\n"
                f"🎁 Награда: <b>+{achievement_reward} ⭐</b>\n\n"
                "<blockquote>"
                "Продолжай выполнять задания "
                "и прокачивай свой уровень."
                "</blockquote>",
                parse_mode="HTML"
            )

    # Получаем новый уровень
    new_profile = get_user_profile(telegram_id)
    new_level = new_profile[5] if new_profile else old_level

    # Проверяем реферала
    referrer_id = get_referrer(telegram_id)

    if referrer_id:

        referral_reward = reward * 25 // 100

        reward_added = add_referral_reward(
            referrer_id,
            telegram_id,
            application_id,
            referral_reward
        )

        if reward_added:

            add_balance(
                referrer_id,
                referral_reward,
                f"Реферальное вознаграждение за заявку #{application_id}"
            )

            add_points(
                referrer_id,
                50
            )

            await bot.send_message(
                referrer_id,
                "👥 <b>Реферальное вознаграждение</b>\n\n"
                "Ваш приглашённый пользователь "
                "выполнил условия предложения.\n\n"
                f"💰 Начислено: "
                f"<b>+{referral_reward:,} ₽</b>\n"
                f"⭐ Баллы: <b>+50</b>\n\n"
                "<blockquote>"
                "Вознаграждение уже доступно "
                "на вашем балансе."
                "</blockquote>",
                parse_mode="HTML"
            )

    # Убираем кнопки у администратора
    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    # Сообщение администратору
    await callback.message.answer(
        f"✅ Заявка #{application_id} подтверждена"
    )

    # Сообщение пользователю
    await bot.send_message(
        telegram_id,
        "✅ <b>Заявка подтверждена</b>\n\n"
        f"<b>{offer_name}</b>\n"
        f"💰 Начислено: <b>+{reward:,} ₽</b>\n"
        f"⭐ Баллы: <b>+100</b>\n\n"
        "<blockquote>"
        "Вознаграждение уже доступно "
        "на вашем балансе."
        "</blockquote>",
        parse_mode="HTML"
    )

    # Уведомление о повышении уровня
    if new_level != old_level:

        await bot.send_message(
            telegram_id,
            "🎉 <b>НОВЫЙ УРОВЕНЬ!</b>\n\n"
            f"Ваш уровень повышен:\n"
            f"<b>{old_level}</b> → <b>{new_level}</b>\n\n"
            "🏆 Вам стали доступны новые возможности.\n\n"
            "Загляните в личный кабинет, "
            "чтобы посмотреть свой прогресс.",
            parse_mode="HTML"
        )

    await callback.answer("Подтверждено")

@dp.callback_query(F.data.startswith("comment_app:"))
async def comment_application(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

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

    if application[7] != "pending":
        await callback.answer(
            "Заявка уже обработана",
            show_alert=True
        )
        return

    await state.clear()

    await state.update_data(
        application_id=application_id
    )

    await state.set_state(
        AdminCommentForm.comment
    )

    await callback.message.answer(
        "💬 <b>КОММЕНТАРИЙ К ЗАЯВКЕ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📄 Заявка: <b>#{application_id}</b>\n\n"
        "Введите комментарий для пользователя.\n\n"
        "<blockquote>"
        "Например: Неверно указаны данные. "
        "Проверьте номер телефона и отправьте заявку повторно."
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("comment_link:"))
async def comment_link_request(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    request_id = int(
        callback.data.split(":")[1]
    )

    link_request = get_link_request(
        request_id
    )

    if not link_request:
        await callback.answer(
            "Запрос не найден",
            show_alert=True
        )
        return

    if link_request[7] != "pending":
        await callback.answer(
            "Запрос уже обработан",
            show_alert=True
        )
        return

    await state.clear()

    await state.update_data(
        link_request_id=request_id
    )

    await state.set_state(
        AdminLinkCommentForm.comment
    )

    await callback.message.answer(
        "💬 <b>КОММЕНТАРИЙ К ЗАПРОСУ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📄 Запрос: <b>#{request_id}</b>\n\n"
        "Введите сообщение для пользователя.\n\n"
        "<blockquote>"
        "Например: проверьте данные и отправьте "
        "запрос повторно."
        "</blockquote>",
        parse_mode="HTML"
    )

    await callback.answer()

@dp.message(AdminLinkCommentForm.comment)
async def save_link_request_comment(
    message: Message,
    state: FSMContext
):
    if message.from_user.id != ADMIN_ID:
        return

    comment = message.text.strip()

    if not comment:
        await message.answer(
            "⚠️ Комментарий не может быть пустым."
        )
        return

    data = await state.get_data()

    request_id = data.get(
        "link_request_id"
    )

    if not request_id:
        await state.clear()

        await message.answer(
            "⚠️ Не удалось определить запрос."
        )
        return

    link_request = get_link_request(
        request_id
    )

    if not link_request:
        await state.clear()

        await message.answer(
            "⚠️ Запрос не найден."
        )
        return

    if link_request[7] != "pending":
        await state.clear()

        await message.answer(
            "⚠️ Этот запрос уже обработан."
        )
        return

    telegram_id = link_request[1]
    offer_id = link_request[2]

    offer = OFFERS.get(offer_id)

    if not offer:
        await state.clear()

        await message.answer(
            "⚠️ Предложение не найдено."
        )
        return

    saved = set_link_request_comment(
        request_id,
        comment
    )

    if not saved:
        await state.clear()

        await message.answer(
            "❌ Не удалось сохранить комментарий."
        )
        return

    await state.clear()

    await bot.send_message(
        telegram_id,
        "💬 <b>СООБЩЕНИЕ ПО ЗАПРОСУ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📄 Запрос: <b>#{request_id}</b>\n"
        f"🏦 Оффер: <b>{offer['name']}</b>\n\n"

        "<b>Комментарий администратора:</b>\n"
        f"{comment}\n\n"

        "<blockquote>"
        "Проверьте информацию и при необходимости "
        "исправьте данные."
        "</blockquote>",

        parse_mode="HTML"
    )

    await message.answer(
        "✅ <b>Комментарий отправлен</b>\n\n"
        f"Запрос: <code>#{request_id}</code>\n"
        f"Пользователь: <code>{telegram_id}</code>",
        parse_mode="HTML"
    )

@dp.message(AdminCommentForm.comment)
async def save_admin_comment(
    message: Message,
    state: FSMContext
):
    if message.from_user.id != ADMIN_ID:
        return

    comment = message.text.strip()

    if not comment:
        await message.answer(
            "⚠️ Комментарий не может быть пустым."
        )
        return

    data = await state.get_data()
    application_id = data.get("application_id")

    if not application_id:
        await state.clear()

        await message.answer(
            "⚠️ Не удалось определить заявку."
        )
        return

    application = get_application(
        application_id
    )

    if not application:
        await state.clear()

        await message.answer(
            "⚠️ Заявка не найдена."
        )
        return

    if application[7] != "pending":
        await state.clear()

        await message.answer(
            "⚠️ Эта заявка уже обработана."
        )
        return

    telegram_id = application[1]
    offer_name = application[2]

    saved = set_application_comment(
        application_id,
        comment
    )

    if not saved:
        await state.clear()

        await message.answer(
            "❌ Не удалось сохранить комментарий."
        )
        return

    await state.clear()

    await bot.send_message(
        telegram_id,
        "💬 <b>КОММЕНТАРИЙ К ЗАЯВКЕ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📄 Заявка: <b>#{application_id}</b>\n"
        f"🏦 Оффер: <b>{offer_name}</b>\n\n"

        "<b>Комментарий администратора:</b>\n"
        f"{comment}\n\n"

        "<blockquote>"
        "Проверьте информацию и при необходимости "
        "исправьте данные."
        "</blockquote>",

        parse_mode="HTML"
    )

    await message.answer(
        "✅ <b>Комментарий отправлен</b>\n\n"
        f"Заявка: <code>#{application_id}</code>\n"
        f"Пользователь: <code>{telegram_id}</code>",
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("reject_app:"))
async def reject_application(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    application_id = int(
        callback.data.split(":")[1]
    )

    application = get_application(application_id)

    if not application:
        await callback.answer("Заявка не найдена")
        return

    if application[7] != "pending":
        await callback.answer(
            "Заявка уже обработана",
            show_alert=True
        )
        return

    telegram_id = application[1]

    update_application_status(
        application_id,
        "rejected"
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await bot.send_message(
        telegram_id,
        "❌ Заявка отклонена\n\n"
        "Условия предложения пока не подтверждены.\n\n"
        "Если произошла ошибка, обратитесь в поддержку."
    )

    await callback.answer("Отклонено")


@dp.message(F.text == "💰 Баланс")
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


@dp.message(F.text == "📋 Мои заявки")
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

@dp.callback_query(F.data == "my_applications")
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

@dp.callback_query(F.data.startswith("application:"))
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

@dp.message(F.text == "💸 Выплата")
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


@dp.callback_query(F.data.startswith("reject_withdrawal:"))
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

@dp.message(F.text == "👨‍💻 Поддержка")
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


@dp.message(F.text == "ℹ️ Как это работает")
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

@dp.callback_query(F.data.startswith("done:"))
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
            ]
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

@dp.callback_query(F.data == "cabinet_apps")
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

@dp.callback_query(F.data == "cabinet_withdraw")
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

@dp.message(WithdrawalForm.amount)
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

@dp.message(WithdrawalForm.phone)
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

@dp.message(WithdrawalForm.bank)
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

async def health_check(request):
    return web.Response(text="BankFlow is running")

@dp.callback_query(F.data.startswith("paid:"))
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

async def main():
    create_tables()

    app = web.Application()
    app.router.add_get("/", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    port = PORT
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"BankFlow запущен ✅ Порт: {port}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
