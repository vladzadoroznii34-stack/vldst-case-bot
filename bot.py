import os
import asyncio
import hashlib
import hmac
import json
import random
import html
from urllib.parse import parse_qsl
from threading import Thread

import psycopg
from flask import Flask, send_from_directory, request

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    Message,
)

from dotenv import load_dotenv


# =========================================================
# ENV
# =========================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(os.getenv("ADMIN_ID", "6038067496"))

PUBLIC_URL = os.getenv(
    "PUBLIC_URL",
    "https://vldst-case-bot.onrender.com"
).rstrip("/")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"{PUBLIC_URL}/webapp/index.html"
)

ADMIN_URL = os.getenv(
    "ADMIN_URL",
    f"{PUBLIC_URL}/webapp/admin.html"
)

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "VLDSTCaseBot"
)


if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден")


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "VLDST CASE Backend is running!"


@app.route("/health")
def health():
    return {
        "status": "ok",
        "project": "VLDST CASE"
    }


@app.route("/webapp/<path:filename>")
def webapp(filename):
    return send_from_directory(
        "webapp",
        filename
    )


# =========================================================
# TELEGRAM WEB APP AUTH
# =========================================================

def verify_telegram_init_data(init_data):
    if not init_data:
        return None

    try:
        data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )

        received_hash = data.pop(
            "hash",
            None
        )

        if not received_hash:
            return None

        check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(data.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        raw_user = data.get("user")

        if not raw_user:
            return None

        return json.loads(raw_user)

    except Exception:
        return None


def get_telegram_user():
    init_data = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    return verify_telegram_init_data(
        init_data
    )


def is_admin():
    user = get_telegram_user()

    if not user:
        return False

    try:
        return int(
            user.get("id", 0)
        ) == ADMIN_ID

    except Exception:
        return False


# =========================================================
# DATABASE
# =========================================================

def init_database():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            # USERS
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS users(
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,

                    coins BIGINT NOT NULL DEFAULT 0,
                    stars BIGINT NOT NULL DEFAULT 0,

                    level INTEGER NOT NULL DEFAULT 1,
                    xp BIGINT NOT NULL DEFAULT 0,

                    referral_code TEXT UNIQUE,
                    referred_by BIGINT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            # CASES
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS cases(
                    id BIGSERIAL PRIMARY KEY,

                    name TEXT NOT NULL,
                    description TEXT,

                    price_coins BIGINT
                    NOT NULL DEFAULT 0,

                    price_stars INTEGER
                    NOT NULL DEFAULT 0,

                    image_url TEXT,

                    active BOOLEAN
                    NOT NULL DEFAULT TRUE,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            # ITEMS
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS items(
                    id BIGSERIAL PRIMARY KEY,

                    name TEXT NOT NULL,
                    description TEXT,

                    rarity TEXT NOT NULL,

                    sell_price BIGINT
                    NOT NULL DEFAULT 0,

                    image_url TEXT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            # CASE ITEMS
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS case_items(
                    id BIGSERIAL PRIMARY KEY,

                    case_id BIGINT NOT NULL
                    REFERENCES cases(id)
                    ON DELETE CASCADE,

                    item_id BIGINT NOT NULL
                    REFERENCES items(id)
                    ON DELETE CASCADE,

                    drop_chance NUMERIC(8,5)
                    NOT NULL
                );
                """
            )

            # INVENTORY
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory(
                    id BIGSERIAL PRIMARY KEY,

                    telegram_id BIGINT NOT NULL
                    REFERENCES users(telegram_id)
                    ON DELETE CASCADE,

                    item_id BIGINT NOT NULL
                    REFERENCES items(id),

                    obtained_from TEXT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            # TRANSACTIONS
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions(
                    id BIGSERIAL PRIMARY KEY,

                    telegram_id BIGINT,

                    type TEXT NOT NULL,

                    amount BIGINT
                    NOT NULL DEFAULT 0,

                    description TEXT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            # =================================================
            # SAFE MIGRATION
            # =================================================

            c.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS stars
                BIGINT NOT NULL DEFAULT 0
                """
            )

            c.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS level
                INTEGER NOT NULL DEFAULT 1
                """
            )

            c.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS xp
                BIGINT NOT NULL DEFAULT 0
                """
            )

            c.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS referral_code
                TEXT
                """
            )

            c.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS referred_by
                BIGINT
                """
            )

            c.execute(
                """
                ALTER TABLE cases
                ADD COLUMN IF NOT EXISTS price_stars
                INTEGER NOT NULL DEFAULT 0
                """
            )

            c.execute(
                """
                ALTER TABLE cases
                ADD COLUMN IF NOT EXISTS image_url
                TEXT
                """
            )

            c.execute(
                """
                ALTER TABLE cases
                ADD COLUMN IF NOT EXISTS active
                BOOLEAN NOT NULL DEFAULT TRUE
                """
            )

            c.execute(
                """
                ALTER TABLE items
                ADD COLUMN IF NOT EXISTS description
                TEXT
                """
            )

            c.execute(
                """
                ALTER TABLE items
                ADD COLUMN IF NOT EXISTS image_url
                TEXT
                """
            )

            # =================================================
            # DEFAULT CASE
            # =================================================

            c.execute(
                "SELECT id FROM cases WHERE id = 1"
            )

            if c.fetchone() is None:

                c.execute(
                    """
                    INSERT INTO cases(
                        id,
                        name,
                        description,
                        price_coins,
                        price_stars,
                        image_url,
                        active
                    )
                    VALUES(
                        1,
                        'VLDST // NEON',
                        'Открой кейс и получи случайный предмет',
                        1000,
                        0,
                        '',
                        TRUE
                    )
                    """
                )

                c.execute(
                    """
                    SELECT setval(
                        pg_get_serial_sequence(
                            'cases',
                            'id'
                        ),
                        GREATEST(
                            (
                                SELECT MAX(id)
                                FROM cases
                            ),
                            1
                        ),
                        true
                    )
                    """
                )

            # =================================================
            # DEFAULT ITEMS
            # =================================================

            seed_items = [

                (
                    "VLDST Neon Tag",
                    "Неоновый тег VLDST",
                    "COMMON",
                    300
                ),

                (
                    "VLDST Pulse",
                    "Энергетический Pulse",
                    "RARE",
                    600
                ),

                (
                    "VLDST Cyber Core",
                    "Кибернетическое ядро",
                    "EPIC",
                    1200
                ),

                (
                    "VLDST Phantom",
                    "Редкий Phantom",
                    "LEGENDARY",
                    2500
                ),

                (
                    "VLDST Void Crown",
                    "Мифическая корона Void",
                    "MYTHIC",
                    5000
                )

            ]

            for (
                name,
                description,
                rarity,
                sell_price
            ) in seed_items:

                c.execute(
                    """
                    SELECT id
                    FROM items
                    WHERE name = %s
                    LIMIT 1
                    """,
                    (name,)
                )

                if c.fetchone() is None:

                    c.execute(
                        """
                        INSERT INTO items(
                            name,
                            description,
                            rarity,
                            sell_price,
                            image_url
                        )
                        VALUES(
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            name,
                            description,
                            rarity,
                            sell_price,
                            ""
                        )
                    )

            # =================================================
            # DEFAULT CHANCES
            # =================================================

            chances = {

                "VLDST Neon Tag": 60.0,
                "VLDST Pulse": 25.0,
                "VLDST Cyber Core": 10.0,
                "VLDST Phantom": 4.5,
                "VLDST Void Crown": 0.5

            }

            c.execute(
                """
                SELECT COUNT(*)
                FROM case_items
                WHERE case_id = 1
                """
            )

            if c.fetchone()[0] == 0:

                for name, chance in chances.items():

                    c.execute(
                        """
                        SELECT id
                        FROM items
                        WHERE name = %s
                        LIMIT 1
                        """,
                        (name,)
                    )

                    row = c.fetchone()

                    if row:

                        c.execute(
                            """
                            INSERT INTO case_items(
                                case_id,
                                item_id,
                                drop_chance
                            )
                            VALUES(
                                1,
                                %s,
                                %s
                            )
                            """,
                            (
                                row[0],
                                chance
                            )
                        )

        conn.commit()


# =========================================================
# USER
# =========================================================

def create_or_update_user(
    telegram_id,
    username,
    first_name,
    referral_id=None
):

    referral_code = (
        f"VLDST{telegram_id}"
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                INSERT INTO users(
                    telegram_id,
                    username,
                    first_name,
                    referral_code,
                    referred_by
                )
                VALUES(
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL
                )

                ON CONFLICT(
                    telegram_id
                )

                DO UPDATE SET
                    username =
                        EXCLUDED.username,

                    first_name =
                        EXCLUDED.first_name

                RETURNING
                    coins,
                    stars,
                    level,
                    xp,
                    referred_by
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    referral_code
                )
            )

            row = c.fetchone()

            # =============================================
            # REFERRAL
            # =============================================

            if (
                referral_id
                and referral_id != telegram_id
                and row[4] is None
            ):

                c.execute(
                    """
                    SELECT telegram_id
                    FROM users
                    WHERE telegram_id = %s
                    """,
                    (referral_id,)
                )

                ref_user = c.fetchone()

                if ref_user:

                    c.execute(
                        """
                        UPDATE users
                        SET
                            referred_by = %s,
                            coins = coins + 500
                        WHERE
                            telegram_id = %s
                            AND referred_by IS NULL
                        """,
                        (
                            referral_id,
                            telegram_id
                        )
                    )

                    if c.rowcount:

                        c.execute(
                            """
                            UPDATE users
                            SET coins = coins + 500
                            WHERE telegram_id = %s
                            """,
                            (referral_id,)
                        )

                        c.execute(
                            """
                            INSERT INTO transactions(
                                telegram_id,
                                type,
                                amount,
                                description
                            )
                            VALUES
                            (
                                %s,
                                'REFERRAL_REWARD',
                                500,
                                'Бонус приглашённому игроку'
                            ),
                            (
                                %s,
                                'REFERRAL_REWARD',
                                500,
                                'Награда за приглашённого игрока'
                            )
                            """,
                            (
                                telegram_id,
                                referral_id
                            )
                        )

            c.execute(
                """
                SELECT
                    coins,
                    stars,
                    level,
                    xp,
                    referred_by
                FROM users
                WHERE telegram_id = %s
                """,
                (telegram_id,)
            )

            row = c.fetchone()

        conn.commit()

    return row


# =========================================================
# USER API
# =========================================================

@app.route("/api/user")
def api_user():

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    coins,
                    stars,
                    level,
                    xp,
                    referral_code,
                    referred_by
                FROM users
                WHERE telegram_id = %s
                """,
                (telegram_id,)
            )

            row = c.fetchone()

    if not row:

        return {
            "error": "user_not_found"
        }, 404

    return {
        "telegram_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "coins": row[3],
        "stars": row[4],
        "level": row[5],
        "xp": row[6],
        "referral_code": row[7],
        "referred_by": row[8]
    }


# =========================================================
# REFERRALS
# =========================================================

@app.route("/api/referrals")
def api_referrals():

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE referred_by = %s
                """,
                (telegram_id,)
            )

            count = c.fetchone()[0]

            c.execute(
                """
                SELECT
                    COALESCE(
                        SUM(amount),
                        0
                    )
                FROM transactions
                WHERE
                    telegram_id = %s
                    AND type = 'REFERRAL_REWARD'
                """,
                (telegram_id,)
            )

            earned = int(
                c.fetchone()[0] or 0
            )

    return {
        "referral_link":
            f"https://t.me/{BOT_USERNAME}?start=ref_{telegram_id}",

        "count":
            count,

        "earned":
            earned
    }


# =========================================================
# CASES
# =========================================================

@app.route("/api/cases")
def api_cases():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image_url
                FROM cases
                WHERE active = TRUE
                ORDER BY id
                """
            )

            rows = c.fetchall()

    return {
        "cases": [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price_coins": row[3],
                "price_stars": row[4],
                "image_url": row[5]
            }
            for row in rows
        ]
    }


@app.route(
    "/api/cases/<int:case_id>/items"
)
def public_case_items(case_id):

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT
                    items.id,
                    items.name,
                    items.description,
                    items.rarity,
                    items.sell_price,
                    items.image_url,
                    case_items.drop_chance

                FROM case_items

                JOIN items
                    ON items.id =
                       case_items.item_id

                WHERE
                    case_items.case_id = %s

                ORDER BY
                    case_items.drop_chance DESC
                """,
                (case_id,)
            )

            rows = c.fetchall()

    return {
        "items": [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "rarity": row[3],
                "sell_price": row[4],
                "image_url": row[5],
                "drop_chance": float(row[6])
            }
            for row in rows
        ]
    }


# =========================================================
# INVENTORY
# =========================================================

@app.route("/api/inventory")
def api_inventory():

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT
                    inventory.id,
                    items.id,
                    items.name,
                    items.description,
                    items.rarity,
                    items.sell_price,
                    items.image_url,
                    inventory.obtained_from,
                    inventory.created_at

                FROM inventory

                JOIN items
                    ON items.id =
                       inventory.item_id

                WHERE
                    inventory.telegram_id = %s

                ORDER BY
                    inventory.created_at DESC
                """,
                (telegram_id,)
            )

            rows = c.fetchall()

    return {
        "inventory": [
            {
                "inventory_id": row[0],
                "item_id": row[1],
                "name": row[2],
                "description": row[3],
                "rarity": row[4],
                "sell_price": row[5],
                "image_url": row[6],
                "obtained_from": row[7],
                "created_at": row[8].isoformat()
            }
            for row in rows
        ]
    }


@app.route(
    "/api/inventory/<int:inventory_id>/sell",
    methods=["POST"]
)
def sell_item(inventory_id):

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT
                    inventory.id,
                    items.name,
                    items.sell_price

                FROM inventory

                JOIN items
                    ON items.id =
                       inventory.item_id

                WHERE
                    inventory.id = %s
                    AND inventory.telegram_id = %s

                FOR UPDATE
                """,
                (
                    inventory_id,
                    telegram_id
                )
            )

            row = c.fetchone()

            if not row:

                return {
                    "error":
                        "inventory_item_not_found"
                }, 404

            sell_price = int(
                row[2] or 0
            )

            if sell_price <= 0:

                return {
                    "error":
                        "item_cannot_be_sold"
                }, 400

            c.execute(
                """
                DELETE FROM inventory
                WHERE
                    id = %s
                    AND telegram_id = %s
                """,
                (
                    inventory_id,
                    telegram_id
                )
            )

            c.execute(
                """
                UPDATE users
                SET coins = coins + %s
                WHERE telegram_id = %s
                RETURNING coins
                """,
                (
                    sell_price,
                    telegram_id
                )
            )

            coins = int(
                c.fetchone()[0]
            )

            c.execute(
                """
                INSERT INTO transactions(
                    telegram_id,
                    type,
                    amount,
                    description
                )
                VALUES(
                    %s,
                    'ITEM_SELL',
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    sell_price,
                    f"Продажа предмета: {row[1]}"
                )
            )

        conn.commit()

    return {
        "success": True,
        "coins": coins,
        "sold_for": sell_price
    }


# =========================================================
# OPEN CASE
# =========================================================

@app.route(
    "/api/cases/<int:case_id>/open",
    methods=["POST"]
)
def open_case(case_id):

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT coins
                FROM users
                WHERE telegram_id = %s
                FOR UPDATE
                """,
                (telegram_id,)
            )

            user_row = c.fetchone()

            if not user_row:

                return {
                    "error":
                        "user_not_found"
                }, 404

            c.execute(
                """
                SELECT
                    id,
                    name,
                    price_coins,
                    price_stars
                FROM cases
                WHERE
                    id = %s
                    AND active = TRUE
                """,
                (case_id,)
            )

            case = c.fetchone()

            if not case:

                return {
                    "error":
                        "case_not_found"
                }, 404

            price = int(
                case[2] or 0
            )

            coins = int(
                user_row[0]
            )

            if coins < price:

                return {
                    "error":
                        "not_enough_coins"
                }, 400

            c.execute(
                """
                SELECT
                    items.id,
                    items.name,
                    items.description,
                    items.rarity,
                    items.sell_price,
                    items.image_url,
                    case_items.drop_chance

                FROM case_items

                JOIN items
                    ON items.id =
                       case_items.item_id

                WHERE
                    case_items.case_id = %s

                ORDER BY
                    case_items.id
                """,
                (case_id,)
            )

            items = c.fetchall()

            if not items:

                return {
                    "error":
                        "case_has_no_items"
                }, 400

            total_chance = sum(
                float(item[6])
                for item in items
            )

            if (
                total_chance <= 0
                or total_chance > 100
            ):

                return {
                    "error":
                        "invalid_drop_chances"
                }, 400

            roll = random.uniform(
                0,
                total_chance
            )

            current = 0

            selected = items[-1]

            for item in items:

                current += float(
                    item[6]
                )

                if roll <= current:

                    selected = item
                    break

            new_coins = (
                coins - price
            )

            c.execute(
                """
                UPDATE users
                SET coins = %s
                WHERE telegram_id = %s
                """,
                (
                    new_coins,
                    telegram_id
                )
            )

            c.execute(
                """
                INSERT INTO inventory(
                    telegram_id,
                    item_id,
                    obtained_from
                )
                VALUES(
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    selected[0],
                    f"case:{case_id}"
                )
            )

            # XP за открытие кейса
            c.execute(
                """
                UPDATE users
                SET
                    xp = xp + 10,
                    level =
                        GREATEST(
                            1,
                            FLOOR(
                                (xp + 10) / 100
                            ) + 1
                        )::INTEGER
                WHERE telegram_id = %s
                """,
                (telegram_id,)
            )

            c.execute(
                """
                INSERT INTO transactions(
                    telegram_id,
                    type,
                    amount,
                    description
                )
                VALUES(
                    %s,
                    'CASE_OPEN',
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    -price,
                    f"Открытие кейса #{case_id}"
                )
            )

        conn.commit()

    return {
        "success": True,

        "coins": new_coins,

        "item": {
            "id": selected[0],
            "name": selected[1],
            "description": selected[2],
            "rarity": selected[3],
            "sell_price": selected[4],
            "image_url": selected[5]
        }
    }


# =========================================================
# ADMIN
# =========================================================

@app.route("/api/admin/check")
def admin_check():

    if not is_admin():

        return {
            "admin": False
        }, 403

    return {
        "admin": True
    }


@app.route("/api/admin/stats")
def admin_stats():

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            result = {}

            for table in (
                "users",
                "cases",
                "items",
                "inventory"
            ):

                c.execute(
                    f"SELECT COUNT(*) FROM {table}"
                )

                result[table] = c.fetchone()[0]

    return result


# =========================================================
# ADMIN GIVE COINS
# =========================================================

@app.route(
    "/api/admin/give-coins",
    methods=["POST"]
)
def admin_give_coins():

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    try:

        telegram_id = int(
            data.get(
                "telegram_id"
            )
        )

        amount = int(
            data.get(
                "amount"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return {
            "error":
                "invalid_data"
        }, 400

    if amount <= 0:

        return {
            "error":
                "amount_must_be_positive"
        }, 400

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                UPDATE users
                SET coins = coins + %s
                WHERE telegram_id = %s
                RETURNING coins
                """,
                (
                    amount,
                    telegram_id
                )
            )

            row = c.fetchone()

            if not row:

                return {
                    "error":
                        "user_not_found"
                }, 404

            coins = int(
                row[0]
            )

            c.execute(
                """
                INSERT INTO transactions(
                    telegram_id,
                    type,
                    amount,
                    description
                )
                VALUES(
                    %s,
                    'ADMIN_GIVE_COINS',
                    %s,
                    'Выдано администратором'
                )
                """,
                (
                    telegram_id,
                    amount
                )
            )

        conn.commit()

    return {
        "success": True,
        "telegram_id": telegram_id,
        "coins": coins,
        "added": amount
    }


# =========================================================
# ADMIN CASES
# =========================================================

@app.route(
    "/api/admin/cases",
    methods=["GET", "POST"]
)
def admin_cases():

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            if request.method == "POST":

                data = (
                    request.get_json(
                        silent=True
                    )
                    or {}
                )

                name = str(
                    data.get(
                        "name",
                        ""
                    )
                ).strip()

                if not name:

                    return {
                        "error":
                            "name_required"
                    }, 400

                try:

                    price_coins = int(
                        data.get(
                            "price_coins",
                            0
                        )
                    )

                    price_stars = int(
                        data.get(
                            "price_stars",
                            0
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return {
                        "error":
                            "invalid_price"
                    }, 400

                if (
                    price_coins < 0
                    or price_stars < 0
                ):

                    return {
                        "error":
                            "invalid_price"
                    }, 400

                c.execute(
                    """
                    INSERT INTO cases(
                        name,
                        description,
                        price_coins,
                        price_stars,
                        image_url
                    )
                    VALUES(
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        name,
                        str(
                            data.get(
                                "description",
                                ""
                            )
                        ),
                        price_coins,
                        price_stars,
                        str(
                            data.get(
                                "image_url",
                                ""
                            )
                        )
                    )
                )

                case_id = c.fetchone()[0]

                conn.commit()

                return {
                    "success": True,
                    "case_id": case_id
                }

            c.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image_url,
                    active

                FROM cases

                ORDER BY id DESC
                """
            )

            rows = c.fetchall()

    return {
        "cases": [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price_coins": row[3],
                "price_stars": row[4],
                "image_url": row[5],
                "active": row[6]
            }
            for row in rows
        ]
    }


@app.route(
    "/api/admin/cases/<int:case_id>/disable",
    methods=["POST"]
)
def disable_case(case_id):

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                UPDATE cases
                SET active = FALSE
                WHERE id = %s
                """,
                (case_id,)
            )

        conn.commit()

    return {
        "success": True
    }


# =========================================================
# ADMIN ITEMS
# =========================================================

@app.route(
    "/api/admin/items",
    methods=["GET", "POST"]
)
def admin_items():

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            if request.method == "POST":

                data = (
                    request.get_json(
                        silent=True
                    )
                    or {}
                )

                name = str(
                    data.get(
                        "name",
                        ""
                    )
                ).strip()

                rarity = str(
                    data.get(
                        "rarity",
                        "COMMON"
                    )
                ).upper().strip()

                try:

                    sell_price = int(
                        data.get(
                            "sell_price",
                            0
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return {
                        "error":
                            "invalid_sell_price"
                    }, 400

                if not name:

                    return {
                        "error":
                            "name_required"
                    }, 400

                if sell_price < 0:

                    return {
                        "error":
                            "invalid_sell_price"
                    }, 400

                if rarity not in {
                    "COMMON",
                    "RARE",
                    "EPIC",
                    "LEGENDARY",
                    "MYTHIC"
                }:

                    return {
                        "error":
                            "invalid_rarity"
                    }, 400

                c.execute(
                    """
                    INSERT INTO items(
                        name,
                        description,
                        rarity,
                        sell_price,
                        image_url
                    )
                    VALUES(
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        name,
                        str(
                            data.get(
                                "description",
                                ""
                            )
                        ),
                        rarity,
                        sell_price,
                        str(
                            data.get(
                                "image_url",
                                ""
                            )
                        )
                    )
                )

                item_id = c.fetchone()[0]

                conn.commit()

                return {
                    "success": True,
                    "item_id": item_id
                }

            c.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    rarity,
                    sell_price,
                    image_url

                FROM items

                ORDER BY id DESC
                """
            )

            rows = c.fetchall()

    return {
        "items": [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "rarity": row[3],
                "sell_price": row[4],
                "image_url": row[5]
            }
            for row in rows
        ]
    }


# =========================================================
# ADMIN ADD ITEM TO CASE
# =========================================================

@app.route(
    "/api/admin/case-items",
    methods=["POST"]
)
def add_case_item():

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    try:

        case_id = int(
            data.get(
                "case_id"
            )
        )

        item_id = int(
            data.get(
                "item_id"
            )
        )

        chance = float(
            data.get(
                "drop_chance"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return {
            "error":
                "invalid_data"
        }, 400

    if (
        chance <= 0
        or chance > 100
    ):

        return {
            "error":
                "invalid_chance"
        }, 400

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT id
                FROM cases
                WHERE id = %s
                """,
                (case_id,)
            )

            if not c.fetchone():

                return {
                    "error":
                        "case_not_found"
                }, 404

            c.execute(
                """
                SELECT id
                FROM items
                WHERE id = %s
                """,
                (item_id,)
            )

            if not c.fetchone():

                return {
                    "error":
                        "item_not_found"
                }, 404

            c.execute(
                """
                SELECT
                    COALESCE(
                        SUM(drop_chance),
                        0
                    )

                FROM case_items

                WHERE case_id = %s
                """,
                (case_id,)
            )

            current_total = float(
                c.fetchone()[0]
            )

            if (
                current_total + chance
                > 100
            ):

                return {
                    "error":
                        "total_chance_exceeds_100"
                }, 400

            c.execute(
                """
                SELECT id
                FROM case_items
                WHERE
                    case_id = %s
                    AND item_id = %s
                """,
                (
                    case_id,
                    item_id
                )
            )

            if c.fetchone():

                return {
                    "error":
                        "item_already_in_case"
                }, 400

            c.execute(
                """
                INSERT INTO case_items(
                    case_id,
                    item_id,
                    drop_chance
                )
                VALUES(
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    case_id,
                    item_id,
                    chance
                )
            )

        conn.commit()

    return {
        "success": True
    }


@app.route(
    "/api/admin/cases/<int:case_id>/items"
)
def admin_case_items(case_id):

    if not is_admin():

        return {
            "error":
                "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as c:

            c.execute(
                """
                SELECT
                    case_items.id,
                    items.id,
                    items.name,
                    items.rarity,
                    case_items.drop_chance

                FROM case_items

                JOIN items
                    ON items.id =
                       case_items.item_id

                WHERE
                    case_items.case_id = %s

                ORDER BY
                    case_items.drop_chance DESC
                """,
                (case_id,)
            )

            rows = c.fetchall()

    items = [
        {
            "case_item_id": row[0],
            "item_id": row[1],
            "name": row[2],
            "rarity": row[3],
            "drop_chance": float(row[4])
        }
        for row in rows
    ]

    total = sum(
        item["drop_chance"]
        for item in items
    )

    return {
        "items": items,
        "total_chance": total,
        "remaining_chance":
            max(0, 100 - total)
    }


# =========================================================
# TELEGRAM BOT
# =========================================================

bot = Bot(
    token=TOKEN
)

dp = Dispatcher()


# =========================================================
# /ADMIN
# =========================================================

@dp.message(
    Command("admin")
)
async def admin_command(
    message: Message
):

    if message.from_user.id != ADMIN_ID:

        await message.answer(
            "⛔ Доступ запрещён."
        )

        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ Открыть админ-панель",
                    web_app=WebAppInfo(
                        url=ADMIN_URL
                    )
                )
            ]
        ]
    )

    await message.answer(
        "🛠 <b>VLDST ADMIN</b>\n\n"
        "Панель управления.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# /START
# =========================================================

@dp.message(
    CommandStart()
)
async def start(
    message: Message
):

    user = message.from_user

    referral_id = None

    parts = message.text.split(
        maxsplit=1
    )

    if (
        len(parts) > 1
        and parts[1].startswith("ref_")
    ):

        try:

            referral_id = int(
                parts[1][4:]
            )

        except ValueError:

            referral_id = None

    (
        coins,
        stars,
        level,
        xp,
        _
    ) = create_or_update_user(
        user.id,
        user.username,
        user.first_name,
        referral_id
    )

    safe_name = html.escape(
        user.first_name or "Игрок"
    )

    buttons = [

        [
            InlineKeyboardButton(
                text="🎁 Открыть VLDST",
                web_app=WebAppInfo(
                    url=WEBAPP_URL
                )
            )
        ]

    ]

    if user.id == ADMIN_ID:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    web_app=WebAppInfo(
                        url=ADMIN_URL
                    )
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await message.answer(
        f"🌌 <b>VLDST CASE</b>\n\n"
        f"Добро пожаловать, "
        f"<b>{safe_name}</b>!\n\n"
        f"🪙 Coins: <b>{coins:,}</b>\n"
        f"⭐ Stars: <b>{stars}</b>\n"
        f"🏆 Уровень: <b>{level}</b>\n"
        f"⚡ XP: <b>{xp}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# WEB SERVER
# =========================================================

def run_web():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )


# =========================================================
# BOT MAIN
# =========================================================

async def main():

    print(
        "Database initialized."
    )

    print(
        "Starting Telegram bot..."
    )

    await dp.start_polling(
        bot
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_database()

    Thread(
        target=run_web,
        daemon=True
    ).start()

    asyncio.run(
        main()
        )
