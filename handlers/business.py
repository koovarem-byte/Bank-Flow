"""Раздел «Для бизнеса»: самозанятость, ИП, РКО, вопросы админу, звонок ВТБ."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMIN_ID
from loader import bot
from offers import OFFERS
from states import (
    BusinessQuestionForm,
    VtbCallForm,
    AdminBusinessAnswerForm
)


router = Router()


@router.callback_query(F.data == "business_step:self")
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

@router.callback_query(F.data == "business_step:registration")
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

@router.callback_query(F.data == "business_guide_registration")
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

@router.callback_query(F.data == "registration_step:documents")
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

@router.callback_query(F.data == "registration_step:how")
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

@router.callback_query(F.data == "registration_step:after")
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

@router.callback_query(F.data == "business_question")
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

@router.message(BusinessQuestionForm.question)
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

@router.callback_query(F.data.startswith("answer_business:"))
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

@router.message(AdminBusinessAnswerForm.answer)
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

@router.callback_query(F.data == "business_step:ip")
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

@router.callback_query(F.data == "business_step:rko")
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

@router.callback_query(F.data == "business_full_guide")
async def business_full_guide(callback: CallbackQuery):

    await callback.answer(
        "Полный гайд пока готовится",
        show_alert=True
    )

@router.callback_query(F.data == "business_guide_self")
async def business_guide_self(callback: CallbackQuery):

    await callback.answer(
        "Гайд по самозанятости пока готовится",
        show_alert=True
    )

@router.callback_query(F.data == "business_guide_ip")
async def business_guide_ip(callback: CallbackQuery):

    await callback.answer(
        "Гайд по ИП пока готовится",
        show_alert=True
    )

@router.callback_query(F.data == "business_guide_rko")
async def business_guide_rko(callback: CallbackQuery):

    await callback.answer(
        "Гайд по РКО пока готовится",
        show_alert=True
    )

@router.callback_query(F.data == "business_offers")
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

@router.callback_query(F.data == "business_guide")
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

@router.callback_query(F.data == "vtb_check_ip")
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

@router.callback_query(F.data == "vtb_ip_yes")
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

@router.callback_query(F.data == "vtb_ip_no")
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

@router.callback_query(F.data == "vtb_call")
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

@router.message(VtbCallForm.time)
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

@router.message(VtbCallForm.phone)
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

@router.callback_query(F.data == "vtb_back_time")
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

@router.callback_query(F.data.startswith("vtb_contact:"))
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

@router.callback_query(F.data.startswith("vtb_done:"))
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
