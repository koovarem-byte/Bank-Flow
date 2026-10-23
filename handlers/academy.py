"""BankFlow Academy."""

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database import get_referral_count, get_active_referral_count


router = Router()


@router.callback_query(F.data == "academy")
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

@router.callback_query(F.data == "academy_1")
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

@router.callback_query(F.data == "academy_2")
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

@router.callback_query(F.data == "academy_3")
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

@router.callback_query(F.data == "academy_4")
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
