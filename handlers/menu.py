"""Старт и главное меню."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    WebAppInfo
)
from config import ADMIN_ID, SUPPORT_URL, WEBAPP_URL
from database import (
    add_user,
    get_balance,
    get_all_users,
    add_referral,
    get_user_profile,
    get_milestone_100,
    set_milestone_100
)
from handlers.onboarding import is_onboarded, send_onboarding
from loader import bot


router = Router()


def with_webapp(keyboard):
    """Кнопка Mini App первой строкой, если задан WEBAPP_URL."""
    if WEBAPP_URL:
        keyboard.inline_keyboard.insert(0, [
            InlineKeyboardButton(
                text="📱 Открыть приложение",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])

    return keyboard


@router.message(CommandStart())
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
    if not is_onboarded(message.from_user.id):
        await send_onboarding(message, message.from_user.id)
        return

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
        reply_markup=with_webapp(keyboard),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "open_offers")
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

@router.callback_query(F.data == "milestone_100")
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

@router.callback_query(F.data == "home")
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

        reply_markup=with_webapp(keyboard),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "how")
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

@router.callback_query(F.data == "about_service")
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
