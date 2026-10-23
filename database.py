import psycopg2

from config import DATABASE_URL

def connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL не найден")

    return psycopg2.connect(DATABASE_URL)


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS level TEXT DEFAULT 'START'
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS total_earned INTEGER DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS age_confirmed_at TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS pd_consent_at TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS pd_consent_version TEXT
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT,
            offer_name TEXT,
            reward INTEGER,
            fio TEXT,
            email TEXT,
            phone TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    cursor.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS admin_comment TEXT
    """)

    cursor.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS offer_id TEXT
    """)

    # Без DEFAULT при добавлении: у старых строк дата неизвестна (NULL),
    # а не дата миграции
    cursor.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE applications
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE applications
        ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT,
            amount INTEGER,
            phone TEXT,
            bank TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_requests (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            offer_id TEXT NOT NULL,
            fio TEXT,
            email TEXT,
            phone TEXT,
            personal_link TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    cursor.execute("""
        ALTER TABLE link_requests
        ALTER COLUMN fio DROP NOT NULL
    """)

    cursor.execute("""
        ALTER TABLE link_requests
        ALTER COLUMN email DROP NOT NULL
    """)

    cursor.execute("""
        ALTER TABLE link_requests
        ALTER COLUMN phone DROP NOT NULL
    """)

    cursor.execute("""
        ALTER TABLE link_requests
        ADD COLUMN IF NOT EXISTS admin_comment TEXT
    """)

    # Без DEFAULT при добавлении: у старых строк дата неизвестна (NULL),
    # а не дата миграции
    cursor.execute("""
        ALTER TABLE link_requests
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE link_requests
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP
    """)

    cursor.execute("""
        ALTER TABLE link_requests
        ADD COLUMN IF NOT EXISTS issued_at TIMESTAMP
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id BIGSERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id BIGSERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT NOT NULL,
            application_id BIGINT NOT NULL UNIQUE,
            amount INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            achievement_code TEXT NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (telegram_id, achievement_code)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_products (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            product_name TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (telegram_id, product_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_history (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            operation_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_balance_history_user
        ON balance_history (telegram_id)
    """)

    conn.commit()
    cursor.close()
    conn.close()

def create_link_request(
    telegram_id,
    offer_id,
    fio=None,
    email=None,
    phone=None
):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO link_requests (
            telegram_id,
            offer_id,
            fio,
            email,
            phone,
            status
        )
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING id
    """, (
        telegram_id,
        offer_id,
        fio,
        email,
        phone
    ))

    request_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return request_id

def has_pending_link_request(telegram_id, offer_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM link_requests
        WHERE telegram_id = %s
        AND offer_id = %s
        AND status = 'pending'
        LIMIT 1
    """, (
        telegram_id,
        offer_id
    ))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None


def get_link_request(request_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            telegram_id,
            offer_id,
            fio,
            email,
            phone,
            personal_link,
            status
        FROM link_requests
        WHERE id = %s
    """, (request_id,))

    request = cursor.fetchone()

    cursor.close()
    conn.close()

    return request


def complete_link_request(request_id, personal_link):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE link_requests
        SET personal_link = %s,
            status = 'ready',
            issued_at = CURRENT_TIMESTAMP
        WHERE id = %s
        AND status = 'pending'
    """, (
        personal_link,
        request_id
    ))

    updated = cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return updated > 0
def add_user(telegram_id, username, full_name):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            full_name
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id) DO NOTHING
    """, (
        telegram_id,
        username,
        full_name
    ))

    conn.commit()
    cursor.close()
    conn.close()


def get_balance(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT balance
        FROM users
        WHERE telegram_id = %s
    """, (telegram_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return result[0]

    return 0


def add_balance(telegram_id, amount, description="Пополнение баланса"):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET balance = balance + %s
        WHERE telegram_id = %s
    """, (
        amount,
        telegram_id
    ))

    cursor.execute("""
        INSERT INTO balance_history (
            telegram_id,
            amount,
            operation_type,
            description
        )
        VALUES (%s, %s, %s, %s)
    """, (
        telegram_id,
        amount,
        "income",
        description
    ))

    conn.commit()
    cursor.close()
    conn.close()


def subtract_balance(telegram_id, amount, description="Списание с баланса"):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET balance = balance - %s
        WHERE telegram_id = %s
        AND balance >= %s
    """, (
        amount,
        telegram_id,
        amount
    ))

    success = cursor.rowcount > 0

    if success:
        cursor.execute("""
            INSERT INTO balance_history (
                telegram_id,
                amount,
                operation_type,
                description
            )
            VALUES (%s, %s, %s, %s)
        """, (
            telegram_id,
            amount,
            "expense",
            description
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return success


def create_application(
    telegram_id,
    offer_name,
    reward,
    fio,
    email,
    phone,
    offer_id=None
):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (
            telegram_id,
            offer_name,
            reward,
            fio,
            email,
            phone,
            offer_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        telegram_id,
        offer_name,
        reward,
        fio,
        email,
        phone,
        offer_id
    ))

    application_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return application_id


def get_application(application_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            telegram_id,
            offer_name,
            reward,
            fio,
            email,
            phone,
            status,
            admin_comment,
            offer_id,
            created_at,
            reviewed_at
        FROM applications
        WHERE id = %s
    """, (application_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


def update_application_status(application_id, status):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET status = %s,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        status,
        application_id
    ))

    conn.commit()
    cursor.close()
    conn.close()


def get_user_applications(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, offer_name, reward, status
        FROM applications
        WHERE telegram_id = %s
        ORDER BY id DESC
    """, (telegram_id,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def has_pending_application(telegram_id, offer_name):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM applications
        WHERE telegram_id = %s
        AND offer_name = %s
        AND status IN ('pending', 'approved')
        LIMIT 1
    """, (
        telegram_id,
        offer_name
    ))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None
def get_pending_withdrawals_total(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM withdrawals
        WHERE telegram_id = %s
        AND status = 'pending'
    """, (telegram_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else 0


def get_available_balance(telegram_id):
    balance = get_balance(telegram_id)
    reserved = get_pending_withdrawals_total(telegram_id)

    return balance - reserved


def create_withdrawal(
    telegram_id,
    amount,
    phone,
    bank
):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO withdrawals (
            telegram_id,
            amount,
            phone,
            bank
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        telegram_id,
        amount,
        phone,
        bank
    ))

    withdrawal_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return withdrawal_id


def get_user_withdrawals(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, amount, phone, bank, status
        FROM withdrawals
        WHERE telegram_id = %s
        ORDER BY id DESC
    """, (telegram_id,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def get_withdrawal(withdrawal_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            telegram_id,
            amount,
            phone,
            bank,
            status
        FROM withdrawals
        WHERE id = %s
    """, (withdrawal_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


def update_withdrawal_status(withdrawal_id, status):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE withdrawals
        SET status = %s
        WHERE id = %s
    """, (
        status,
        withdrawal_id
    ))

    conn.commit()
    cursor.close()
    conn.close()


def get_users_count():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else 0


def get_all_users():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT telegram_id, username, full_name, balance
        FROM users
        ORDER BY telegram_id DESC
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return users
def get_admin_stats():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            COUNT(*),
            COUNT(*) FILTER (WHERE status = 'pending'),
            COUNT(*) FILTER (WHERE status = 'approved'),
            COUNT(*) FILTER (WHERE status = 'rejected')
        FROM applications
    """)
    applications = cursor.fetchone()

    cursor.execute("""
        SELECT
            COUNT(*),
            COUNT(*) FILTER (WHERE status = 'pending'),
            COUNT(*) FILTER (WHERE status = 'paid'),
            COUNT(*) FILTER (WHERE status = 'rejected'),
            COALESCE(
                SUM(amount) FILTER (WHERE status = 'paid'),
                0
            )
        FROM withdrawals
    """)
    withdrawals = cursor.fetchone()

    cursor.execute("""
        SELECT
            COUNT(*),
            COUNT(*) FILTER (WHERE status = 'pending')
        FROM link_requests
    """)
    links = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "users": users,

        "applications_total": applications[0],
        "applications_pending": applications[1],
        "applications_approved": applications[2],
        "applications_rejected": applications[3],

        "withdrawals_total": withdrawals[0],
        "withdrawals_pending": withdrawals[1],
        "withdrawals_paid": withdrawals[2],
        "withdrawals_rejected": withdrawals[3],
        "withdrawals_paid_amount": withdrawals[4],

        "links_total": links[0],
        "links_pending": links[1]
    }
def get_user_growth_stats():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) FILTER (
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
            ),
            COUNT(*) FILTER (
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            ),
            COUNT(*) FILTER (
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            ),
            COUNT(*)
        FROM users
    """)

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "today": result[0],
        "week": result[1],
        "month": result[2],
        "total": result[3]
    }
def add_referral(referrer_id, referred_id):
    if referrer_id == referred_id:
        return False

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO referrals (referrer_id, referred_id)
        VALUES (%s, %s)
        ON CONFLICT (referred_id) DO NOTHING
        """,
        (referrer_id, referred_id)
    )

    added = cursor.rowcount > 0

    conn.commit()
    cursor.close()
    conn.close()

    return added

def get_referral_count(referrer_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer_id = %s
        """,
        (referrer_id,)
    )

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count
def get_referrer(referred_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT referrer_id
        FROM referrals
        WHERE referred_id = %s
        """,
        (referred_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return result[0]

    return None
def add_referral_reward(
    referrer_id,
    referred_id,
    application_id,
    amount
):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO referral_rewards (
            referrer_id,
            referred_id,
            application_id,
            amount
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (application_id) DO NOTHING
        """,
        (
            referrer_id,
            referred_id,
            application_id,
            amount
        )
    )

    added = cursor.rowcount > 0

    conn.commit()
    cursor.close()
    conn.close()

    return added
def get_active_referral_count(referrer_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(DISTINCT r.referred_id)
        FROM referrals r
        JOIN applications a
            ON a.telegram_id = r.referred_id
        WHERE r.referrer_id = %s
        AND a.status = 'approved'
        """,
        (referrer_id,)
    )

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count
def get_user_profile(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            telegram_id,
            username,
            full_name,
            balance,
            points,
            level,
            total_earned
        FROM users
        WHERE telegram_id = %s
    """, (telegram_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result


def add_points(telegram_id, amount):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET points = GREATEST(points + %s, 0)
        WHERE telegram_id = %s
        RETURNING points
    """, (amount, telegram_id))

    result = cursor.fetchone()

    if result:
        points = result[0]

        if points >= 6000:
            level = "LEGEND"
        elif points >= 3000:
            level = "MASTER"
        elif points >= 1500:
            level = "ELITE"
        elif points >= 500:
            level = "PRO"
        else:
            level = "START"

        cursor.execute("""
            UPDATE users
            SET level = %s
            WHERE telegram_id = %s
        """, (level, telegram_id))

    conn.commit()
    cursor.close()
    conn.close()

def add_total_earned(telegram_id, amount):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET total_earned = total_earned + %s
        WHERE telegram_id = %s
    """, (amount, telegram_id))

    conn.commit()
    cursor.close()
    conn.close()


def set_user_level(telegram_id, level):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET level = %s
        WHERE telegram_id = %s
    """, (level, telegram_id))

    conn.commit()
    cursor.close()
    conn.close()

def add_achievement(telegram_id, achievement_code):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO achievements (
            telegram_id,
            achievement_code
        )
        VALUES (%s, %s)
        ON CONFLICT (telegram_id, achievement_code)
        DO NOTHING
        RETURNING id
    """, (
        telegram_id,
        achievement_code
    ))

    result = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return result is not None


def get_user_achievements(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            achievement_code,
            earned_at
        FROM achievements
        WHERE telegram_id = %s
        ORDER BY earned_at DESC
    """, (telegram_id,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result

def add_user_product(telegram_id, product_name):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user_products (
            telegram_id,
            product_name
        )
        VALUES (%s, %s)
        ON CONFLICT (telegram_id, product_name)
        DO NOTHING
    """, (
        telegram_id,
        product_name
    ))

    conn.commit()
    cursor.close()
    conn.close()

def get_user_products(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT product_name
        FROM user_products
        WHERE telegram_id = %s
        ORDER BY added_at DESC
    """, (telegram_id,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        product[0]
        for product in result
    ]

def get_milestone_100():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM achievements
        WHERE telegram_id = 0
        AND achievement_code = 'milestone_100'
        LIMIT 1
    """)

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None


def set_milestone_100():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO achievements (
            telegram_id,
            achievement_code
        )
        VALUES (0, 'milestone_100')
        ON CONFLICT (telegram_id, achievement_code)
        DO NOTHING
    """)

    conn.commit()
    cursor.close()
    conn.close()

def set_application_comment(application_id, comment):
        conn = connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE applications
            SET admin_comment = %s
            WHERE id = %s
        """, (
            comment,
            application_id
        ))

        updated = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        return updated > 0

def get_application_comment(application_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT admin_comment
        FROM applications
        WHERE id = %s
    """, (application_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return None

    return result[0]

def set_link_request_comment(request_id, comment):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE link_requests
        SET admin_comment = %s
        WHERE id = %s
    """, (
        comment,
        request_id
    ))

    updated = cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return updated > 0


def get_onboarding_status(telegram_id):
    """(возраст подтверждён, версия согласия на обработку ПД или None)."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT age_confirmed_at, pd_consent_version
        FROM users
        WHERE telegram_id = %s
    """, (telegram_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return False, None

    return result[0] is not None, result[1]


def confirm_age(telegram_id, username, full_name):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            full_name,
            age_confirmed_at
        )
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (telegram_id) DO UPDATE
        SET age_confirmed_at = COALESCE(
            users.age_confirmed_at,
            CURRENT_TIMESTAMP
        )
    """, (
        telegram_id,
        username,
        full_name
    ))

    conn.commit()
    cursor.close()
    conn.close()


def set_pd_consent(telegram_id, version):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET pd_consent_at = CURRENT_TIMESTAMP,
            pd_consent_version = %s
        WHERE telegram_id = %s
    """, (
        version,
        telegram_id
    ))

    updated = cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return updated > 0


def get_link_issued_at(telegram_id, offer_id):
    """Когда пользователю последний раз выдали ссылку на оффер (или None)."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(issued_at)
        FROM link_requests
        WHERE telegram_id = %s
        AND offer_id = %s
    """, (
        telegram_id,
        offer_id
    ))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else None


def get_user_applications_detailed(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            offer_id,
            offer_name,
            reward,
            status,
            admin_comment,
            created_at,
            reviewed_at
        FROM applications
        WHERE telegram_id = %s
        ORDER BY id DESC
    """, (telegram_id,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def get_user_link_requests(telegram_id):
    """Последний запрос ссылки по каждому офферу."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (offer_id)
            offer_id,
            status,
            personal_link,
            admin_comment,
            issued_at
        FROM link_requests
        WHERE telegram_id = %s
        ORDER BY offer_id, id DESC
    """, (telegram_id,))

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result
