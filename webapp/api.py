"""JSON API для Mini App. Авторизация — initData от Telegram в заголовке
`Authorization: tma <initData>`. Пока нет 18+ и согласия на ПД, доступны
только /api/me, /api/privacy и /api/onboarding/*.
"""

import os
import re

from aiohttp import web

from config import BOT_TOKEN
from database import (
    add_user,
    add_referral,
    get_user_profile,
    get_onboarding_status,
    confirm_age,
    set_pd_consent,
    get_available_balance,
    get_user_applications_detailed,
    get_user_link_requests,
    get_user_withdrawals,
    get_referral_count,
    get_active_referral_count,
    get_user_achievements,
    has_pending_link_request,
    create_link_request,
    has_pending_application,
    create_application,
    get_link_issued_at,
    create_withdrawal
)
from handlers.onboarding import is_onboarded, mark_onboarded
from loader import bot
from notifications import (
    notify_link_request,
    notify_application,
    notify_withdrawal
)
from offers import (
    OFFERS,
    CATEGORIES,
    is_credit_offer,
    get_erid,
    SAFETY_RULE,
    CREDIT_WARNING
)
from privacy import PRIVACY_VERSION, PRIVACY_PARTS, CONSENT_TEXT
from progress import ACHIEVEMENTS, level_progress
from webapp.auth import validate_init_data


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

OPEN_PATHS = {"/api/me", "/api/privacy", "/api/onboarding/age", "/api/onboarding/consent"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_bot_username = None


def error(status, code, message):
    return web.json_response(
        {"error": code, "message": message},
        status=status
    )


def digits(value):
    return "".join(ch for ch in value if ch.isdigit())


def iso(value):
    return value.isoformat() if value else None


@web.middleware
async def auth_middleware(request, handler):
    if not request.path.startswith("/api/"):
        return await handler(request)

    header = request.headers.get("Authorization", "")
    init_data = header[4:] if header.startswith("tma ") else ""

    data = validate_init_data(init_data, BOT_TOKEN)

    if not data:
        return error(401, "unauthorized", "Откройте приложение из Telegram")

    request["tg_user"] = data["user"]
    request["start_param"] = data.get("start_param")

    if request.path not in OPEN_PATHS and not is_onboarded(data["user"]["id"]):
        return error(403, "onboarding_required", "Подтвердите возраст и согласие")

    return await handler(request)


async def read_json(request):
    try:
        body = await request.json()
    except Exception:
        return {}

    return body if isinstance(body, dict) else {}


def offer_payload(offer_id, offer, link_state=None):
    link = None
    link_status = None
    admin_comment = None

    if link_state:
        link_status, link, admin_comment = link_state

    if offer_id == "vtb_rko":
        flow = "bot"
    elif offer.get("access") == "personal":
        flow = "personal"
    else:
        flow = "request"

    return {
        "id": offer_id,
        "name": offer["name"],
        "type": offer["type"],
        "category": offer["category"],
        "reward": offer["reward"],
        "min_age": offer.get("min_age"),
        "max_age": offer.get("max_age"),
        "condition": offer["condition"],
        "requirements": offer.get("requirements", []),
        "flow": flow,
        "is_credit": is_credit_offer(offer),
        "ad": {
            "advertiser": offer.get("advertiser") or offer["name"],
            "erid": get_erid(link) or get_erid(offer.get("link")),
            "terms_url": offer.get("terms_url")
        },
        "link_status": link_status,
        "link": link if link_status == "ready" else None,
        "link_comment": admin_comment
    }


async def me(request):
    user = request["tg_user"]
    user_id = user["id"]

    full_name = " ".join(
        part for part in (user.get("first_name"), user.get("last_name")) if part
    )

    add_user(user_id, user.get("username"), full_name)

    start_param = request["start_param"] or ""

    if start_param.startswith("ref_"):
        try:
            add_referral(int(start_param[4:]), user_id)
        except ValueError:
            pass

    profile = get_user_profile(user_id)
    age_ok, consent_version = get_onboarding_status(user_id)

    balance = profile[3] or 0
    points = profile[4] or 0
    level = profile[5] or "START"
    total_earned = profile[6] or 0

    return web.json_response({
        "id": user_id,
        "first_name": user.get("first_name") or "",
        "onboarding": {
            "age_confirmed": age_ok,
            "consent": consent_version == PRIVACY_VERSION
        },
        "balance": balance,
        "available": get_available_balance(user_id),
        "total_earned": total_earned,
        "points": points,
        "progress": level_progress(level, points)
    })


async def privacy(request):
    return web.json_response({
        "version": PRIVACY_VERSION,
        "parts": PRIVACY_PARTS,
        "consent": CONSENT_TEXT
    })


async def onboarding_age(request):
    user = request["tg_user"]

    full_name = " ".join(
        part for part in (user.get("first_name"), user.get("last_name")) if part
    )

    confirm_age(user["id"], user.get("username"), full_name)

    return web.json_response({"ok": True})


async def onboarding_consent(request):
    user_id = request["tg_user"]["id"]

    age_ok, _ = get_onboarding_status(user_id)

    if not age_ok:
        return error(400, "age_required", "Сначала подтвердите возраст")

    set_pd_consent(user_id, PRIVACY_VERSION)
    mark_onboarded(user_id)

    return web.json_response({"ok": True})


async def offers(request):
    user_id = request["tg_user"]["id"]

    link_states = {
        row[0]: (row[1], row[2], row[3])
        for row in get_user_link_requests(user_id)
    }

    return web.json_response({
        "categories": [
            {"id": key, "name": value["name"], "icon": value["icon"]}
            for key, value in CATEGORIES.items()
        ],
        "offers": [
            offer_payload(offer_id, offer, link_states.get(offer_id))
            for offer_id, offer in OFFERS.items()
        ],
        "safety_rule": SAFETY_RULE,
        "credit_warning": CREDIT_WARNING
    })


async def request_link(request):
    user = request["tg_user"]
    offer_id = request.match_info["offer_id"]
    offer = OFFERS.get(offer_id)

    if not offer or offer_id == "vtb_rko":
        return error(404, "offer_not_found", "Предложение не найдено")

    if has_pending_link_request(user["id"], offer_id):
        return error(409, "already_requested", "Запрос уже отправлен — ссылка готовится")

    fio = email = phone = None

    if offer.get("access") == "personal":
        body = await read_json(request)

        fio = str(body.get("fio", "")).strip()
        email = str(body.get("email", "")).strip()
        phone = str(body.get("phone", "")).strip()

        if not 5 <= len(fio) <= 150 or len(fio.split()) < 2:
            return error(400, "bad_fio", "Укажите фамилию, имя и отчество")

        if len(email) > 150 or not EMAIL_RE.match(email):
            return error(400, "bad_email", "Проверьте email")

        if not 10 <= len(digits(phone)) <= 15 or len(phone) > 30:
            return error(400, "bad_phone", "Проверьте номер телефона")

    request_id = create_link_request(
        telegram_id=user["id"],
        offer_id=offer_id,
        fio=fio,
        email=email,
        phone=phone
    )

    await notify_link_request(request_id, offer, user, fio, email, phone)

    return web.json_response({"ok": True, "request_id": request_id})


async def offer_done(request):
    user = request["tg_user"]
    offer_id = request.match_info["offer_id"]
    offer = OFFERS.get(offer_id)

    if not offer:
        return error(404, "offer_not_found", "Предложение не найдено")

    link_issued_at = get_link_issued_at(user["id"], offer_id)

    if not link_issued_at:
        return error(400, "no_link", "Сначала получите ссылку и оформите продукт")

    if has_pending_application(user["id"], offer["name"]):
        return error(409, "already_sent", "Вы уже отправляли заявку по этому предложению")

    application_id = create_application(
        telegram_id=user["id"],
        offer_name=offer["name"],
        reward=offer["reward"],
        fio="",
        email="",
        phone="",
        offer_id=offer_id
    )

    await notify_application(application_id, offer_id, offer, user, link_issued_at)

    return web.json_response({"ok": True, "application_id": application_id})


async def applications(request):
    rows = get_user_applications_detailed(request["tg_user"]["id"])

    return web.json_response({
        "applications": [
            {
                "id": row[0],
                "offer_id": row[1],
                "offer_name": row[2],
                "reward": row[3],
                "status": row[4],
                "comment": row[5],
                "created_at": iso(row[6]),
                "reviewed_at": iso(row[7])
            }
            for row in rows
        ]
    })


async def withdrawals(request):
    rows = get_user_withdrawals(request["tg_user"]["id"])

    return web.json_response({
        "withdrawals": [
            {"id": row[0], "amount": row[1], "bank": row[3], "status": row[4]}
            for row in rows
        ]
    })


async def create_withdrawal_request(request):
    user = request["tg_user"]
    body = await read_json(request)

    try:
        amount = int(str(body.get("amount", "")).replace(" ", ""))
    except ValueError:
        return error(400, "bad_amount", "Введите сумму цифрами")

    phone = str(body.get("phone", "")).strip()
    bank = str(body.get("bank", "")).strip()

    if amount <= 0:
        return error(400, "bad_amount", "Сумма должна быть больше 0 ₽")

    available = get_available_balance(user["id"])

    if amount > available:
        return error(400, "not_enough", f"Доступно для вывода: {available:,} ₽")

    if not 10 <= len(digits(phone)) <= 15 or len(phone) > 30:
        return error(400, "bad_phone", "Проверьте номер телефона")

    if not 2 <= len(bank) <= 60:
        return error(400, "bad_bank", "Укажите банк")

    withdrawal_id = create_withdrawal(
        telegram_id=user["id"],
        amount=amount,
        phone=phone,
        bank=bank
    )

    await notify_withdrawal(withdrawal_id, amount, phone, bank, user)

    return web.json_response({"ok": True, "withdrawal_id": withdrawal_id})


async def referrals(request):
    global _bot_username

    user_id = request["tg_user"]["id"]

    if not _bot_username:
        _bot_username = (await bot.get_me()).username

    return web.json_response({
        "invited": get_referral_count(user_id),
        "active": get_active_referral_count(user_id),
        "link": f"https://t.me/{_bot_username}?start=ref_{user_id}",
        "percent": 25
    })


async def achievements(request):
    earned = {row[0]: row[1] for row in get_user_achievements(request["tg_user"]["id"])}

    return web.json_response({
        "achievements": [
            {
                "code": code,
                "title": title,
                "description": description,
                "reward": reward,
                "earned_at": iso(earned.get(code))
            }
            for code, title, description, reward in ACHIEVEMENTS
        ]
    })


async def index(request):
    return web.FileResponse(os.path.join(STATIC_DIR, "index.html"))


def setup_webapp(app):
    app.middlewares.append(auth_middleware)

    app.router.add_get("/api/me", me)
    app.router.add_get("/api/privacy", privacy)
    app.router.add_post("/api/onboarding/age", onboarding_age)
    app.router.add_post("/api/onboarding/consent", onboarding_consent)
    app.router.add_get("/api/offers", offers)
    app.router.add_post("/api/offers/{offer_id}/link", request_link)
    app.router.add_post("/api/offers/{offer_id}/done", offer_done)
    app.router.add_get("/api/applications", applications)
    app.router.add_get("/api/withdrawals", withdrawals)
    app.router.add_post("/api/withdrawals", create_withdrawal_request)
    app.router.add_get("/api/referrals", referrals)
    app.router.add_get("/api/achievements", achievements)

    app.router.add_get("/app", index)
    app.router.add_get("/app/", index)
    app.router.add_static("/app/static", STATIC_DIR)
