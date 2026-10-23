MAGNIT_LINK = "https://lk.bs-rko.ru/click?q=MzY0Nnxwcm9kdWN0"

OFFERS = {
    "magnit_pay": {
        "name": "Магнит Пэй",
        "category": "debit",
        "type": "Дебетовая карта",

        "reward": 1000,

        "min_age": 18,
        "max_age": None,

        "access": "personal",
        "link": None,

        "condition": (
            "Совершить покупку одним чеком от 500 ₽ "
            "и оплатить её картой Магнит Пэй."
        ),

        "requirements": [
            "ФИО",
            "Email",
            "Номер телефона"
        ]
    },

    "psb_debit": {
        "name": "ПСБ",
        "category": "debit",
        "type": "Дебетовая карта",

        "reward": 900,

        "min_age": 18,
        "max_age": None,

        "access": "direct",
        "link": "https://rko-group.ru/s/wYtLyrdl",

        "condition": (
            "Совершить покупки на общую сумму от 1 000 ₽. "
            "Покупки можно совершать несколькими чеками."
        ),

        "requirements": []
    },

    "ak_bars_debit": {
        "name": "Ак Барс Банк",
        "category": "debit",
        "type": "Дебетовая карта",

        "reward": 850,

        "min_age": 18,
        "max_age": None,

        "access": "direct",
        "link": (
            "https://t.fincpanetwork.ru/click/32507/397"
            "?erid=2VfnxvVWi3a"
        ),

        "condition": (
            "Совершить покупку одним чеком "
            "на сумму от 1 000 ₽."
        ),

        "requirements": []
    },

    "rshb_unionpay": {
        "name": "Россельхозбанк — UnionPay",
        "category": "debit",
        "type": "Дебетовая карта",

        "reward": 700,

        "min_age": 18,
        "max_age": None,

        "access": "direct",
        "link": (
            "https://t.fincpanetwork.ru/click/32507/930"
            "?erid=2W5zFGdgfuj"
        ),

        "condition": (
            "Совершить покупку одним чеком "
            "на сумму от 100 ₽."
        ),

        "requirements": []
    },

    "alfa_debit": {
        "name": "Альфа-Банк",
        "category": "debit",
        "type": "Дебетовая карта",

        "reward": 1000,

        "min_age": 18,
        "max_age": None,

        "access": "direct",
        "link": "https://alfa.me/Sy2XP2",

        "condition": (
            "Совершить 5 любых покупок по карте. "
            "Минимальная сумма покупки — от 10 ₽."
        ),

        "requirements": []
    },

    "tbank_credit": {
        "name": "Т-Банк",
        "category": "credit",
        "type": "Кредитная карта",

        "reward": 2000,

        "min_age": 18,
        "max_age": 70,

        "access": "direct",
        "link": (
            "https://t.fincpanetwork.ru/click/32507/27"
            "?erid=2W5zFKAWohb"
        ),

        "condition": (
            "Совершить покупку одним чеком "
            "на сумму от 1 000 ₽ по карте."
        ),

        "requirements": []
    },

    "alfa_credit": {
        "name": "Альфа-Банк",
        "category": "credit",
        "type": "Кредитная карта",

        "reward": 1800,

        "min_age": 18,
        "max_age": None,

        "access": "direct",
        "link": (
            "https://t.fincpanetwork.ru/click/32507/339"
            "?erid=2W5zFJjJPEG"
        ),

        "condition": (
            "Совершить любую покупку по карте "
            "через терминал."
        ),

        "requirements": []
    },

"zenit_credit": {
    "name": "Зенит Банк",
    "category": "credit",
    "type": "Кредитная карта",
    "reward": 2000,
    "min_age": 21,
    "max_age": None,
    "access": "personal",
    "link": None,
    "condition": (
        "Получение кредитной карты "
        "с лимитом от 30 000 ₽."
    ),
    "requirements": [
        "ФИО",
        "Email",
        "Номер телефона"
    ]
},

"uralsib_credit": {
    "name": "Уралсиб",
    "category": "credit",
    "type": "Кредитная карта",
    "reward": 2000,
    "min_age": 18,
    "max_age": None,
    "access": "personal",
    "link": None,
    "condition": (
        "Совершить транзакцию от 500 ₽ "
        "в течение 30 дней с момента выдачи карты."
    ),
    "requirements": [
        "ФИО",
        "Email",
        "Номер телефона"
    ]
},

    "yandex_split": {
        "name": "Яндекс Сплит",
        "category": "credit",
        "type": "Оплата частями",

        "reward": 2000,

        "min_age": 18,
        "max_age": 70,
"access": "direct",
        "link": (
            "https://trk.ppdu.ru/click/QJrdGxj5"
            "?erid=2SDnjdJuo9L"
        ),

        "condition": (
            "Совершить оплату на сумму от 1 000 ₽ "
            "в течение 30 дней."
        ),

        "requirements": []
    },

    "belka_credit": {
        "name": "Белка Кредит",
        "category": "mfo",
        "type": "МФО",

        "reward": 2000,

        "min_age": 18,
        "max_age": None,

        "access": "direct",
        "link": (
            "https://t.fincpanetwork.ru/click/32507/918"
            "?erid=2W5zFK43c2V"
        ),

        "condition": (
            "Оформить и получить займ "
            "на сумму от 1 000 ₽ без процентов."
        ),

        "requirements": []
    },"vtb_rko": {
    "name": "ВТБ",
    "category": "business",
    "type": "РКО",
    "reward": 3000,
    "min_age": 18,
    "max_age": None,
    "access": "manual",
    "link": None,
    "condition": (
        "Активировать бесплатный расчётный счёт."
    ),
    "requirements": []
},
}


CATEGORIES = {
    "debit": {
        "name": "Дебетовые карты",
        "icon": "💳"
    },

    "credit": {
        "name": "Кредитные карты",
        "icon": "💳"
    },

    "mfo": {
        "name": "МФО",
        "icon": "₽"
    },

    "invest": {
        "name": "Инвестиции",
        "icon": "📈"
    },

    "business": {
        "name": "Для бизнеса",
        "icon": "🏢"
    }
}