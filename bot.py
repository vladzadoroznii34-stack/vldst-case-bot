import os
import asyncio
import hashlib
import hmac
import json
import random
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
ADMIN_ID = int(os.getenv("ADMIN_ID", "6038067496"))

WEBAPP_URL = (
    "https://vldst-case-bot.onrender.com/"
    "webapp/index.html"
)

ADMIN_URL = (
    "https://vldst-case-bot.onrender.com/"
    "webapp/admin.html"
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
    return "VLDST Backend is running!"


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

        user_data = data.get("user")

        if not user_data:
            return None

        return json.loads(user_data)

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
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            # USERS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,

                    telegram_id BIGINT
                    UNIQUE NOT NULL,

                    username TEXT,

                    first_name TEXT,

                    coins BIGINT
                    NOT NULL DEFAULT 0,

                    stars BIGINT
                    NOT NULL DEFAULT 0,

                    level INTEGER
                    NOT NULL DEFAULT 1,

                    xp BIGINT
                    NOT NULL DEFAULT 0,

                    referral_code TEXT
                    UNIQUE,

                    referred_by BIGINT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
            """)

            # CASES
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cases (
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
            """)

            # ITEMS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
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
            """)

            # CASE ITEMS
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

            # INVENTORY
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

            # TRANSACTIONS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,

                    telegram_id BIGINT,

                    type TEXT NOT NULL,

                    amount BIGINT
                    NOT NULL DEFAULT 0,

                    description TEXT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
            """)

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

                ON CONFLICT (telegram_id)

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
# API: USER
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
                    xp
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
        "xp": row[6]
    }


# =========================================================
# API: CASES
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

    result = []

    for row in rows:

        result.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price_coins": row[3],
            "price_stars": row[4],
            "image_url": row[5]
        })

    return {
        "cases": result
    }


# =========================================================
# API: INVENTORY
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

    inventory = []

    for row in rows:

        inventory.append({
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
        })

    return {
        "inventory": inventory
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

            # USER
            cur.execute(
                """
                SELECT
                    coins,
                    stars
                FROM users
                WHERE telegram_id = %s
                FOR UPDATE
                """,
                (telegram_id,)
            )

            user_row = cur.fetchone()

            if not user_row:
                return {
                    "error": "user_not_found"
                }, 404

            coins = int(
                user_row[0]
            )

            # CASE
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
                    "error": "case_not_found"
                }, 404

            price_coins = int(
                case_row[2] or 0
            )

            # CHECK COINS
            if coins < price_coins:
                return {
                    "error":
                        "not_enough_coins"
                }, 400

            # ITEMS
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

                WHERE
                    case_items.case_id = %s
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

            # RANDOM DROP
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

            # REMOVE COINS
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

            # ADD ITEM
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

            # TRANSACTION
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
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    "CASE_OPEN",
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
# ADMIN CHECK
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


# =========================================================
# ADMIN STATS
# =========================================================

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
            "error": "invalid_data"
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
                SELECT coins
                FROM users
                WHERE telegram_id = %s
                FOR UPDATE
                """,
                (telegram_id,)
            )

            user = cur.fetchone()

            if not user:
                return {
                    "error":
                        "user_not_found"
                }, 404

            old_coins = int(
                user[0]
            )

            new_coins = (
                old_coins +
                amount
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
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    telegram_id,
                    "ADMIN_GIVE_COINS",
                    amount,
                    "Выдано администратором"
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
# ADMIN GET CASES
# =========================================================

@app.route("/api/admin/cases")
def admin_get_cases():

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

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
                    image_url,
                    active
                FROM cases
                ORDER BY id DESC
                """
            )

            rows = cur.fetchall()

    result = []

    for row in rows:

        result.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price_coins": row[3],
            "price_stars": row[4],
            "image_url": row[5],
            "active": row[6]
        })

    return {
        "cases": result
    }


# =========================================================
# ADMIN CREATE CASE
# =========================================================

@app.route(
    "/api/admin/cases",
    methods=["POST"]
)
def admin_create_case():

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    image_url = str(
        data.get("image_url", "")
    ).strip()

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

    except (TypeError, ValueError):

        return {
            "error": "invalid_price"
        }, 400

    if not name:
        return {
            "error": "name_required"
        }, 400

    if price_coins < 0:
        return {
            "error":
                "price_must_be_positive"
        }, 400

    if price_stars < 0:
        return {
            "error":
                "price_must_be_positive"
        }, 400

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO cases
                (
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image_url
                )

                VALUES
                (
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
                    description,
                    price_coins,
                    price_stars,
                    image_url
                )
            )

            case_id = cur.fetchone()[0]

        conn.commit()

    return {
        "success": True,
        "case_id": case_id
    }


# =========================================================
# ADMIN DISABLE CASE
# =========================================================

@app.route(
    "/api/admin/cases/<int:case_id>/disable",
    methods=["POST"]
)
def admin_disable_case(case_id):

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
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
# ADMIN GET ITEMS
# =========================================================

@app.route("/api/admin/items")
def admin_get_items():

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

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
                    rarity,
                    sell_price,
                    image_url
                FROM items
                ORDER BY id DESC
                """
            )

            rows = cur.fetchall()

    result = []

    for row in rows:

        result.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "rarity": row[3],
            "sell_price": row[4],
            "image_url": row[5]
        })

    return {
        "items": result
    }


# =========================================================
# ADMIN CREATE ITEM
# =========================================================

@app.route(
    "/api/admin/items",
    methods=["POST"]
)
def admin_create_item():

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get("name", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    rarity = str(
        data.get(
            "rarity",
            "COMMON"
        )
    ).strip().upper()

    image_url = str(
        data.get("image_url", "")
    ).strip()

    try:

        sell_price = int(
            data.get(
                "sell_price",
                0
            )
        )

    except (TypeError, ValueError):

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
                "sell_price_must_be_positive"
        }, 400

    allowed_rarities = {
        "COMMON",
        "RARE",
        "EPIC",
        "LEGENDARY",
        "MYTHIC"
    }

    if rarity not in allowed_rarities:
        return {
            "error":
                "invalid_rarity"
        }, 400

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO items
                (
                    name,
                    description,
                    rarity,
                    sell_price,
                    image_url
                )

                VALUES
                (
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
                    description,
                    rarity,
                    sell_price,
                    image_url
                )
            )

            item_id = cur.fetchone()[0]

        conn.commit()

    return {
        "success": True,
        "item_id": item_id
    }


# =========================================================
# ADMIN ADD ITEM TO CASE
# =========================================================

@app.route(
    "/api/admin/case-items",
    methods=["POST"]
)
def admin_add_case_item():

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

    data = request.get_json(
        silent=True
    ) or {}

    try:

        case_id = int(
            data.get("case_id")
        )

        item_id = int(
            data.get("item_id")
        )

        drop_chance = float(
            data.get("drop_chance")
        )

    except (TypeError, ValueError):

        return {
            "error": "invalid_data"
        }, 400

    if drop_chance <= 0:
        return {
            "error":
                "chance_must_be_positive"
        }, 400

    if drop_chance > 100:
        return {
            "error":
                "chance_cannot_exceed_100"
        }, 400

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM cases
                WHERE id = %s
                """,
                (case_id,)
            )

            if not cur.fetchone():
                return {
                    "error":
                        "case_not_found"
                }, 404

            cur.execute(
                """
                SELECT id
                FROM items
                WHERE id = %s
                """,
                (item_id,)
            )

            if not cur.fetchone():
                return {
                    "error":
                        "item_not_found"
                }, 404

            cur.execute(
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

            current_sum = float(
                cur.fetchone()[0]
            )

            if (
                current_sum +
                drop_chance >
                100
            ):
                return {
                    "error":
                        "total_chance_exceeds_100"
                }, 400

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
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    case_id,
                    item_id,
                    drop_chance
                )
            )

        conn.commit()

    return {
        "success": True
    }


# =========================================================
# ADMIN CASE CONTENT
# =========================================================

@app.route(
    "/api/admin/cases/<int:case_id>/items"
)
def admin_case_items(case_id):

    if not is_admin():
        return {
            "error": "forbidden"
        }, 403

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
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

            rows = cur.fetchall()

    result = []

    for row in rows:

        result.append({
            "case_item_id": row[0],
            "item_id": row[1],
            "name": row[2],
            "rarity": row[3],
            "drop_chance":
                float(row[4])
        })

    total = sum(
        item["drop_chance"]
        for item in result
    )

    return {
        "items": result,
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
        "Панель управления проектом.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start(
    message: Message
):

    user = message.from_user

    coins, stars, level, xp = (
        create_or_update_user(
            user.id,
            user.username,
            user.first_name
        )
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
        f"🌌 <b>VLDST</b>\n\n"
        f"Добро пожаловать, "
        f"<b>{user.first_name}</b>!\n\n"
        f"🪙 Coins: "
        f"<b>{coins:,}</b>\n"
        f"⭐ Stars: "
        f"<b>{stars}</b>\n"
        f"⭐ Уровень: "
        f"<b>{level}</b>\n"
        f"⚡ XP: "
        f"<b>{xp}</b>",
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
        port=port
    )


# =========================================================
# START
# =========================================================

async def main():

    print("Initializing database...")

    init_database()

    print("Database initialized.")

    print("Starting Telegram bot...")

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
