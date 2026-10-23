import asyncio

from aiohttp import web

from aiogram import Dispatcher

from config import PORT
from database import create_tables
from handlers import routers
from loader import bot


dp = Dispatcher()
dp.include_routers(*routers)


async def health_check(request):
    return web.Response(text="BankFlow is running")


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
