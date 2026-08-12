import os
import asyncio
import hashlib
import hmac
import json
import random
import secrets

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
# CONFIG
# =========================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "6038067496"
    )
)

BOT_USERNAME = "VLDSTCaseBot"

BASE_URL = "https://vldst-case-bot.onrender.com"

WEBAPP_URL = (
    BASE_URL +
    "/webapp/index.html"
)

ADMIN_URL = (
    BASE_URL +
    "/webapp/admin.html"
)


if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден"
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не найден"
    )


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return {
        "status": "ok",
        "project": "VLDST CASE"
    }


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
# TELEGRAM WEBAPP AUTH
# =========================================================

def verify_telegram_init_data(
    init_data
):

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

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(
                data.items()
            )
        )

        secret_key = hmac.new(
            b"WebAppData",
            TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user_data = data.get(
            "user"
        )

        if not user_data:
            return None

        return json.loads(
            user_data
        )

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
        return (
            int(user.get("id", 0))
            == ADMIN_ID
        )
    except Exception:
        return False


# =========================================================
# DATABASE
# =========================================================

def init_database():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
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
                    referral_earnings BIGINT NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS
                referral_earnings BIGINT
                NOT NULL DEFAULT 0;
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price_coins BIGINT NOT NULL DEFAULT 0,
                    price_stars INTEGER NOT NULL DEFAULT 0,
                    image_url TEXT,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    rarity TEXT NOT NULL,
                    sell_price BIGINT NOT NULL DEFAULT 0,
                    image_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS case_items (
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
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
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
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,

                    telegram_id BIGINT,

                    type TEXT NOT NULL,

                    amount BIGINT NOT NULL DEFAULT 0,

                    description TEXT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
            """)

        conn.commit()


# =========================================================
# DEFAULT CASE
# =========================================================

def create_default_content():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                "SELECT id FROM cases WHERE id = 1"
            )

            case = cur.fetchone()

            if not case:

                cur.execute("""
                    INSERT INTO cases
                    (
                        id,
                        name,
                        description,
                        price_coins,
                        price_stars,
                        active
                    )
                    VALUES
                    (
                        1,
                        'VLDST // NEON',
                        'VLDST Neon Case',
                        1000,
                        15,
                        TRUE
                    )
                """)

            items_data = [
                (
                    "VLDST Neon Tag",
                    "Неоновый предмет VLDST",
                    "COMMON",
                    150
                ),
                (
                    "VLDST Pulse",
                    "Импульсный предмет VLDST",
                    "RARE",
                    400
                ),
                (
                    "VLDST Cyber Core",
                    "Ядро VLDST",
                    "EPIC",
                    1000
                ),
                (
                    "VLDST Phantom",
                    "Легендарный Phantom",
                    "LEGENDARY",
                    3000
                ),
                (
                    "VLDST Void Crown",
                    "Мифическая корона",
                    "MYTHIC",
                    10000
                )
            ]

            item_ids = []

            for item in items_data:

                cur.execute(
                    """
                    SELECT id
                    FROM items
                    WHERE name = %s
                    """,
                    (item[0],)
                )

                existing = cur.fetchone()

                if existing:
                    item_ids.append(
                        existing[0]
                    )
                else:

                    cur.execute(
                        """
                        INSERT INTO items
                        (
                            name,
                            description,
                            rarity,
                            sell_price
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        RETURNING id
                        """,
                        item
                    )

                    item_ids.append(
                        cur.fetchone()[0]
                    )

            chances = [
                60,
                25,
                10,
                4.5,
                0.5
            ]

            for item_id, chance in zip(
                item_ids,
                chances
            ):

                cur.execute(
                    """
                    SELECT id
                    FROM case_items
                    WHERE case_id = 1
                    AND item_id = %s
                    """,
                    (item_id,)
                )

                existing = cur.fetchone()

                if not existing:

                    cur.execute(
                        """
                        INSERT INTO case_items
                        (
                            case_id,
                            item_id,
                            drop_chance
                        )
                        VALUES
                        (
                            1,
                            %s,
                            %s
                        )
                        """,
                        (
                            item_id,
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
    first_name
):

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            referral_code = (
                f"VLDST{telegram_id}"
            )

            cur.execute(
                """
                INSERT INTO users
                (
                    telegram_id,
                    username,
                    first_name,
                    referral_code
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )

                ON CONFLICT (
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
                    xp
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    referral_code
                )
            )

            result = cur.fetchone()

        conn.commit()

    return result


# =========================================================
# START / REFERRAL
# =========================================================

@dp_message_placeholder = None


def process_referral(
    new_user_id,
    referral_code
):

    if not referral_code:
        return

    if not referral_code.startswith(
        "VLDST"
    ):
        return

    try:
        inviter_id = int(
            referral_code.replace(
                "VLDST",
                ""
            )
        )
    except ValueError:
        return

    if inviter_id == new_user_id:
        return

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT referred_by
                FROM users
                WHERE telegram_id = %s
                """,
                (new_user_id,)
            )

            user = cur.fetchone()

            if not user:
                return

            if user[0] is not None:
                return

            cur.execute(
                """
                SELECT telegram_id
                FROM users
                WHERE telegram_id = %s
                """,
                (inviter_id,)
            )

            inviter = cur.fetchone()

            if not inviter:
                return

            cur.execute(
                """
                UPDATE users
                SET referred_by = %s
                WHERE telegram_id = %s
                """,
                (
                    inviter_id,
                    new_user_id
                )
            )

        conn.commit()


# =========================================================
# API USER
# =========================================================

@app.route("/api/user")
def api_user():

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user.get("id")
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
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
                    referral_earnings
                FROM users
                WHERE telegram_id = %s
                """,
                (telegram_id,)
            )

            row = cur.fetchone()

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
        "referral_earnings": row[8]
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
        user.get("id")
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    referral_code,
                    referral_earnings
                FROM users
                WHERE telegram_id = %s
                """,
                (telegram_id,)
            )

            row = cur.fetchone()

            if not row:
                return {
                    "error":
                        "user_not_found"
                }, 404

            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE referred_by = %s
                """,
                (telegram_id,)
            )

            invited = cur.fetchone()[0]

    return {
        "referral_code": row[0],
        "link":
            f"https://t.me/{BOT_USERNAME}"
            f"?start={row[0]}",
        "invited": invited,
        "earnings": row[1]
    }


# =========================================================
# CASES
# =========================================================

@app.route("/api/cases")
def api_cases():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
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
                ORDER BY id ASC
                """
            )

            rows = cur.fetchall()

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
        user.get("id")
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
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

            rows = cur.fetchall()

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
                "created_at":
                    row[8].isoformat()
            }
            for row in rows
        ]
    }


# =========================================================
# SELL ITEM
# =========================================================

@app.route(
    "/api/inventory/<int:inventory_id>/sell",
    methods=["POST"]
)
def sell_inventory_item(
    inventory_id
):

    user = get_telegram_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user.get("id")
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    inventory.item_id,
                    items.name,
                    items.sell_price
                FROM inventory

                JOIN items
                ON items.id =
                   inventory.item_id

                WHERE inventory.id = %s
                AND inventory.telegram_id = %s

                FOR UPDATE
                """,
                (
                    inventory_id,
                    telegram_id
                )
            )

            item = cur.fetchone()

            if not item:
                return {
                    "error":
                        "inventory_item_not_found"
                }, 404

            sell_price = int(
                item[2] or 0
            )

            if sell_price <= 0:
                return {
                    "error":
                        "item_cannot_be_sold"
                }, 400

            cur.execute(
                """
                SELECT coins
                FROM users
                WHERE telegram_id = %s
                FOR UPDATE
                """,
                (telegram_id,)
            )

            user_row = cur.fetchone()

            if not user_row:
                return {
                    "error":
                        "user_not_found"
                }, 404

            new_coins = (
                int(user_row[0]) +
                sell_price
            )

            cur.execute(
                """
                DELETE FROM inventory
                WHERE id = %s
                AND telegram_id = %s
                """,
                (
                    inventory_id,
                    telegram_id
                )
            )

            cur.execute(
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

            cur.execute(
                """
                INSERT INTO transactions
                (
                    telegram_id,
                    type,
                    amount,
                    description
                )
                VALUES
                (
                    %s,
                    'ITEM_SELL',
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    sell_price,
                    f"Продан предмет: {item[1]}"
                )
            )

        conn.commit()

    return {
        "success": True,
        "coins": new_coins,
        "added": sell_price
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
        user.get("id")
    )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT coins
                FROM users
                WHERE telegram_id = %s
                FOR UPDATE
                """,
                (telegram_id,)
            )

            user_row = cur.fetchone()

            if not user_row:
                return {
                    "error":
                        "user_not_found"
                }, 404

            coins = int(
                user_row[0]
            )

            cur.execute(
                """
                SELECT
                    id,
                    name,
                    price_coins,
                    price_stars
                FROM cases
                WHERE id = %s
                AND active = TRUE
                """,
                (case_id,)
            )

            case_row = cur.fetchone()

            if not case_row:
                return {
                    "error":
                        "case_not_found"
                }, 404

            price_coins = int(
                case_row[2] or 0
            )

            if coins < price_coins:
                return {
                    "error":
                        "not_enough_coins"
                }, 400

            cur.execute(
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

                WHERE case_items.case_id = %s
                """,
                (case_id,)
            )

            items = cur.fetchall()

            if not items:
                return {
                    "error":
                        "case_has_no_items"
                }, 400

            total_chance = sum(
                float(item[6])
                for item in items
            )

            if total_chance <= 0:
                return {
                    "error":
                        "invalid_drop_chances"
                }, 400

            roll = random.uniform(
                0,
                total_chance
            )

            current = 0
            selected = None

            for item in items:

                current += float(
                    item[6]
                )

                if roll <= current:
                    selected = item
                    break

            if selected is None:
                selected = items[-1]

            item_id = selected[0]

            new_coins = (
                coins -
                price_coins
            )

            cur.execute(
                """
                UPDATE users
                SET coins = %s,
                    xp = xp + 10
                WHERE telegram_id = %s
                """,
                (
                    new_coins,
                    telegram_id
                )
            )

            cur.execute(
                """
                INSERT INTO inventory
                (
                    telegram_id,
                    item_id,
                    obtained_from
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    item_id,
                    f"case:{case_id}"
                )
            )

            cur.execute(
                """
                INSERT INTO transactions
                (
                    telegram_id,
                    type,
                    amount,
                    description
                )
                VALUES
                (
                    %s,
                    'CASE_OPEN',
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    -price_coins,
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
            "error": "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                "SELECT COUNT(*) FROM users"
            )
            users = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM cases"
            )
            cases = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM items"
            )
            items = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM inventory"
            )
            inventory = cur.fetchone()[0]

    return {
        "users": users,
        "cases": cases,
        "items": items,
        "inventory": inventory
    }


@app.route(
    "/api/admin/give-coins",
    methods=["POST"]
)
def admin_give_coins():

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

    data = request.get_json(
        silent=True
    ) or {}

    try:

        telegram_id = int(
            data.get("telegram_id")
        )

        amount = int(
            data.get("amount")
        )

    except (TypeError, ValueError):

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

        with conn.cursor() as cur:

            cur.execute(
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

            row = cur.fetchone()

            if not row:
                return {
                    "error":
                        "user_not_found"
                }, 404

            new_coins = int(
                row[0]
            )

            cur.execute(
                """
                INSERT INTO transactions
                (
                    telegram_id,
                    type,
                    amount,
                    description
                )
                VALUES
                (
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
        "coins": new_coins,
        "added": amount
    }


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=TOKEN
)

dp = Dispatcher()


@dp.message(Command("admin"))
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
                    text="⚙️ Открыть VLDST ADMIN",
                    web_app=WebAppInfo(
                        url=ADMIN_URL
                    )
                )
            ]
        ]
    )

    await message.answer(
        "🛠 <b>VLDST ADMIN</b>\n\n"
        "Панель управления проектом.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.message(CommandStart())
async def start(
    message: Message
):

    user = message.from_user

    create_or_update_user(
        user.id,
        user.username,
        user.first_name
    )

    command_args = (
        message.text.split(maxsplit=1)
    )

    if len(command_args) > 1:

        process_referral(
            user.id,
            command_args[1].strip()
        )

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    coins,
                    stars,
                    level,
                    xp
                FROM users
                WHERE telegram_id = %s
                """,
                (user.id,)
            )

            coins, stars, level, xp = (
                cur.fetchone()
            )

    buttons = [
        [
            InlineKeyboardButton(
                text="🚀 ОТКРЫТЬ VLDST",
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
                    text="⚙️ VLDST ADMIN",
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
        f"<b>{user.first_name}</b>!\n\n"
        f"🪙 Coins: <b>{coins:,}</b>\n"
        f"⭐ Stars: <b>{stars}</b>\n"
        f"🏆 Level: <b>{level}</b>\n"
        f"⚡ XP: <b>{xp}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# SERVER
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
        port=port
    )


async def main():

    print(
        "Initializing VLDST database..."
    )

    init_database()

    create_default_content()

    print(
        "Database initialized."
    )

    print(
        "Starting VLDST bot..."
    )

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":

    web_thread = Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    asyncio.run(
        main()
        )
