"""Роутеры бота. Порядок важен: обработчики сообщений без фильтра
состояния срабатывают в любом FSM-состоянии, поэтому проверяются по очереди."""

from handlers import menu
from handlers import admin
from handlers import academy
from handlers import business
from handlers import catalog
from handlers import cabinet
from handlers import legacy
from handlers import withdrawals


routers = [
    menu.router,
    admin.router,
    academy.router,
    business.router,
    catalog.router,
    cabinet.router,
    legacy.router,
    withdrawals.router
]
