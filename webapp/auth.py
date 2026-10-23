"""Проверка initData от Telegram Mini App.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
hash       = hex(HMAC_SHA256(key=secret_key, msg=data_check_string))
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data, bot_token, max_age=24 * 60 * 60):
    """Возвращает dict с полями initData (user — уже dict) или None."""
    if not init_data:
        return None

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)

    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(pairs.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        return None

    if max_age and time.time() - auth_date > max_age:
        return None

    try:
        pairs["user"] = json.loads(pairs["user"])
    except (KeyError, ValueError):
        return None

    if not isinstance(pairs["user"], dict) or "id" not in pairs["user"]:
        return None

    return pairs
