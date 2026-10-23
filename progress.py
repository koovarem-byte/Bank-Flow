"""Уровни и достижения — в том же виде, что показывает бот.

Используется Mini App. В handlers/* те же значения пока записаны
внутри обработчиков; при правке менять в обоих местах (свести — отдельной задачей).
"""

# уровень: (баллы начала уровня, баллы следующего уровня, следующий уровень)
LEVELS = {
    "START": (0, 500, "PRO"),
    "PRO": (500, 1500, "ELITE"),
    "ELITE": (1500, 3000, "MASTER"),
    "MASTER": (3000, 6000, "LEGEND"),
    "LEGEND": (6000, 6000, None)
}

# (код, название, описание, награда в баллах)
ACHIEVEMENTS = [
    ("first_earning", "Первый заработок", "Получите первое вознаграждение", 100),
    ("500_points", "500 баллов", "Наберите 500 ⭐", 150),
    ("10k_earned", "Первые 10 000 ₽", "Заработайте 10 000 ₽", 300),
    ("5_referrals", "5 рефералов", "Пригласите 5 пользователей", 250)
]


def level_progress(level, points):
    level = level if level in LEVELS else "START"
    current, target, next_level = LEVELS[level]

    if not next_level:
        return {
            "level": level,
            "next_level": None,
            "percent": 100,
            "remaining": 0,
            "target": target
        }

    percent = int((points - current) / (target - current) * 100)

    return {
        "level": level,
        "next_level": next_level,
        "percent": max(0, min(100, percent)),
        "remaining": max(0, target - points),
        "target": target
    }
