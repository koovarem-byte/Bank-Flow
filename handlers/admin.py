"""Админка: пользователи, статистика, заявки, комментарии, рассылка."""

import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMIN_ID
from database import (
    get_link_request,
    add_balance,
    subtract_balance,
    get_application,
    update_application_status,
    get_user_applications,
    get_users_count,
    get_all_users,
    get_admin_stats,
    get_user_growth_stats,
    get_referral_count,
    get_referrer,
    add_referral_reward,
    get_user_profile,
    add_points,
    add_total_earned,
    set_user_level,
    add_achievement,
    set_application_comment,
    set_link_request_comment
)
from loader import bot
from offers import OFFERS
from states import (
    AdminCommentForm,
    AdminLinkCommentForm,
    AdminUserForm
)


router = Router()


@router.message(F.text == "/admin")
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

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    await show_admin_users(callback, page=0)

@router.callback_query(F.data.startswith("admin_users_page:"))
async def admin_users_page(callback: CallbackQuery):

    page = int(callback.data.split(":")[1])

    await show_admin_users(callback, page=page)

@router.callback_query(F.data == "admin_stats")
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

@router.callback_query(F.data.startswith("admin_user:"))
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

@router.callback_query(F.data.startswith("admin_points:"))
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

@router.callback_query(F.data.startswith("admin_balance:"))
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

@router.callback_query(F.data.startswith("admin_level:"))
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

@router.callback_query(F.data.startswith("admin_earned:"))
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

@router.message(AdminUserForm.value)
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

@router.callback_query(F.data == "admin_panel")
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

@router.message(Command("broadcast100"))
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

@router.callback_query(F.data.startswith("approve_app:"))
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

@router.callback_query(F.data.startswith("comment_app:"))
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

@router.callback_query(F.data.startswith("comment_link:"))
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

@router.message(AdminLinkCommentForm.comment)
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

@router.message(AdminCommentForm.comment)
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

@router.callback_query(F.data.startswith("reject_app:"))
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
