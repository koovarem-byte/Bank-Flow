import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def _require(name):
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"Не задана переменная окружения {name}. "
            "Скопируй .env.example в .env и заполни, "
            "или задай её в настройках хостинга."
        )

    return value


BOT_TOKEN = _require("BOT_TOKEN")
DATABASE_URL = _require("DATABASE_URL")

try:
    ADMIN_ID = int(_require("ADMIN_ID"))
except ValueError:
    raise RuntimeError("ADMIN_ID должен быть числом (Telegram ID админа)")

SUPPORT_USERNAME = _require("SUPPORT_USERNAME").lstrip("@")
SUPPORT_URL = f"https://t.me/{SUPPORT_USERNAME}"

PORT = int(os.getenv("PORT", "10000"))

# HTTPS-адрес Mini App (…/app/). Пусто — кнопки приложения в боте нет.
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
