import os
import asyncio
import threading
import random
import hashlib
import hmac
import json
from urllib.parse import parse_qsl

import psycopg
from flask import Flask, jsonify, request, send_from_directory

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0")

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 0

print("BOT_TOKEN exists:", bool(TOKEN))
print("DATABASE_URL exists:", bool(DATABASE_URL))
print("ADMIN_ID:", ADMIN_ID)

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден. Проверь Environment Variables в Render."
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не найден. Проверь PostgreSQL и Environment Variables в Render."
    )


# =========================================================
# URL
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBAPP_DIR = os.path.join(BASE_DIR, "webapp")

WEBAPP_URL = "https://vldst-case-bot.onrender.com/webapp/index.html"
ADMIN_URL = "https://vldst-case-bot.onrender.com/webapp/admin.html"


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "VLDST Backend is running!"


@app.route("/webapp/<path:filename>")
def webapp(filename):
    return send_from_directory(WEBAPP_DIR, filename)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "bot_token": bool(TOKEN),
        "database": bool(DATABASE_URL)
    })


# =========================================================
# DATABASE
# =========================================================

def get_db():
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    coins BIGINT DEFAULT 0,
                    stars BIGINT DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    xp BIGINT DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    referred_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    price_coins BIGINT DEFAULT 0,
                    price_stars BIGINT DEFAULT 0,
                    image TEXT DEFAULT '',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    rarity TEXT DEFAULT 'common',
                    sell_price BIGINT DEFAULT 0,
                    image TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS case_items (
                    id BIGSERIAL PRIMARY KEY,
                    case_id BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                    drop_chance DOUBLE PRECISION DEFAULT 1
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT NOT NULL,
                    type TEXT NOT NULL,
                    amount BIGINT DEFAULT 0,
                    description TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.commit()


# =========================================================
# USER
# =========================================================

def make_referral_code(telegram_id):
    raw = f"VLDST-{telegram_id}-{random.randint(1000, 9999)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:10]


def get_or_create_user(
    telegram_id,
    username=None,
    first_name=None,
    referral_code=None
):
    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
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
            """, (telegram_id,))

            user = cur.fetchone()

            if user:
                cur.execute("""
                    UPDATE users
                    SET username = %s,
                        first_name = %s
                    WHERE telegram_id = %s
                """, (
                    username,
                    first_name,
                    telegram_id
                ))

                conn.commit()
                return get_user(telegram_id)

            new_code = make_referral_code(telegram_id)

            referred_by = None

            if referral_code:
                cur.execute("""
                    SELECT telegram_id
                    FROM users
                    WHERE referral_code = %s
                """, (referral_code,))

                ref_user = cur.fetchone()

                if ref_user and ref_user[0] != telegram_id:
                    referred_by = ref_user[0]

            cur.execute("""
                INSERT INTO users (
                    telegram_id,
                    username,
                    first_name,
                    coins,
                    stars,
                    level,
                    xp,
                    referral_code,
                    referred_by
                )
                VALUES (%s, %s, %s, 0, 0, 1, 0, %s, %s)
            """, (
                telegram_id,
                username,
                first_name,
                new_code,
                referred_by
            ))

        conn.commit()

    return get_user(telegram_id)


def get_user(telegram_id):
    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
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
            """, (telegram_id,))

            row = cur.fetchone()

            if not row:
                return None

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
# TELEGRAM WEBAPP AUTH
# =========================================================

def validate_telegram_data(init_data):
    if not init_data:
        return None

    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))

        received_hash = data.pop("hash", None)

        if not received_hash:
            return None

        data_check_string = "\n".join(
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

    except Exception as e:
        print("Telegram auth error:", e)
        return None


def get_webapp_user():
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        init_data = request.args.get("initData")

    user_data = validate_telegram_data(init_data)

    if not user_data:
        return None

    telegram_id = int(user_data["id"])

    return get_or_create_user(
        telegram_id,
        user_data.get("username"),
        user_data.get("first_name")
    )


# =========================================================
# API USER
# =========================================================

@app.route("/api/user")
def api_user():

    user = get_webapp_user()

    if not user:
        return jsonify({
            "error": "Unauthorized"
        }), 401

    return jsonify(user)


# =========================================================
# CASES
# =========================================================

@app.route("/api/cases")
def api_cases():

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image,
                    active
                FROM cases
                WHERE active = TRUE
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

    result = []

    for row in rows:
        result.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price_coins": row[3],
            "price_stars": row[4],
            "image": row[5],
            "active": row[6]
        })

    return jsonify(result)


# =========================================================
# OPEN CASE
# =========================================================

@app.route("/api/cases/<int:case_id>/open", methods=["POST"])
def open_case(case_id):

    user = get_webapp_user()

    if not user:
        return jsonify({
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    currency = data.get("currency", "coins")

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    price_coins,
                    price_stars
                FROM cases
                WHERE id = %s
                  AND active = TRUE
            """, (case_id,))

            case = cur.fetchone()

            if not case:
                return jsonify({
                    "error": "Case not found"
                }), 404

            price_coins = case[2]
            price_stars = case[3]

            if currency == "stars":

                if user["stars"] < price_stars:
                    return jsonify({
                        "error": "Недостаточно Stars"
                    }), 400

                cur.execute("""
                    UPDATE users
                    SET stars = stars - %s
                    WHERE telegram_id = %s
                """, (
                    price_stars,
                    user["telegram_id"]
                ))

                cur.execute("""
                    INSERT INTO transactions
                    (telegram_id, type, amount, description)
                    VALUES (%s, 'case_open', %s, %s)
                """, (
                    user["telegram_id"],
                    -price_stars,
                    f"Открытие кейса {case[1]}"
                ))

            else:

                if user["coins"] < price_coins:
                    return jsonify({
                        "error": "Недостаточно Coins"
                    }), 400

                cur.execute("""
                    UPDATE users
                    SET coins = coins - %s
                    WHERE telegram_id = %s
                """, (
                    price_coins,
                    user["telegram_id"]
                ))

                cur.execute("""
                    INSERT INTO transactions
                    (telegram_id, type, amount, description)
                    VALUES (%s, 'case_open', %s, %s)
                """, (
                    user["telegram_id"],
                    -price_coins,
                    f"Открытие кейса {case[1]}"
                ))

            cur.execute("""
                SELECT
                    ci.item_id,
                    ci.drop_chance,
                    i.name,
                    i.description,
                    i.rarity,
                    i.sell_price,
                    i.image
                FROM case_items ci
                JOIN items i ON i.id = ci.item_id
                WHERE ci.case_id = %s
            """, (case_id,))

            items = cur.fetchall()

            if not items:
                conn.rollback()

                return jsonify({
                    "error": "В кейсе пока нет предметов"
                }), 400

            total_chance = sum(
                float(item[1])
                for item in items
            )

            roll = random.uniform(
                0,
                total_chance
            )

            current = 0
            selected = None

            for item in items:
                current += float(item[1])

                if roll <= current:
                    selected = item
                    break

            if not selected:
                selected = items[-1]

            cur.execute("""
                INSERT INTO inventory
                (user_id, item_id)
                VALUES (%s, %s)
            """, (
                user["telegram_id"],
                selected[0]
            ))

            cur.execute("""
                UPDATE users
                SET xp = xp + 10
                WHERE telegram_id = %s
            """, (
                user["telegram_id"],
            ))

            conn.commit()

    return jsonify({
        "success": True,
        "item": {
            "id": selected[0],
            "name": selected[2],
            "description": selected[3],
            "rarity": selected[4],
            "sell_price": selected[5],
            "image": selected[6]
        }
    })


# =========================================================
# INVENTORY
# =========================================================

@app.route("/api/inventory")
def api_inventory():

    user = get_webapp_user()

    if not user:
        return jsonify({
            "error": "Unauthorized"
        }), 401

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    inv.id,
                    i.id,
                    i.name,
                    i.description,
                    i.rarity,
                    i.sell_price,
                    i.image,
                    inv.obtained_at
                FROM inventory inv
                JOIN items i ON i.id = inv.item_id
                WHERE inv.user_id = %s
                ORDER BY inv.id DESC
            """, (
                user["telegram_id"],
            ))

            rows = cur.fetchall()

    result = []

    for row in rows:
        result.append({
            "id": row[0],
            "item_id": row[1],
            "name": row[2],
            "description": row[3],
            "rarity": row[4],
            "sell_price": row[5],
            "image": row[6],
            "obtained_at": str(row[7])
        })

    return jsonify(result)


# =========================================================
# SELL ITEM
# =========================================================

@app.route(
    "/api/inventory/<int:inventory_id>/sell",
    methods=["POST"]
)
def sell_item(inventory_id):

    user = get_webapp_user()

    if not user:
        return jsonify({
            "error": "Unauthorized"
        }), 401

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    inv.id,
                    i.name,
                    i.sell_price
                FROM inventory inv
                JOIN items i ON i.id = inv.item_id
                WHERE inv.id = %s
                  AND inv.user_id = %s
            """, (
                inventory_id,
                user["telegram_id"]
            ))

            item = cur.fetchone()

            if not item:
                return jsonify({
                    "error": "Предмет не найден"
                }), 404

            sell_price = item[2]

            cur.execute("""
                DELETE FROM inventory
                WHERE id = %s
            """, (
                inventory_id,
            ))

            cur.execute("""
                UPDATE users
                SET coins = coins + %s
                WHERE telegram_id = %s
            """, (
                sell_price,
                user["telegram_id"]
            ))

            cur.execute("""
                INSERT INTO transactions
                (telegram_id, type, amount, description)
                VALUES (%s, 'item_sell', %s, %s)
            """, (
                user["telegram_id"],
                sell_price,
                f"Продажа предмета {item[1]}"
            ))

        conn.commit()

    return jsonify({
        "success": True,
        "coins": sell_price
    })


# =========================================================
# ADMIN CHECK
# =========================================================

@app.route("/api/admin/check")
def admin_check():

    user = get_webapp_user()

    if not user:
        return jsonify({
            "admin": False
        }), 401

    return jsonify({
        "admin": user["telegram_id"] == ADMIN_ID
    })


def require_admin():

    user = get_webapp_user()

    if not user:
        return None

    if user["telegram_id"] != ADMIN_ID:
        return None

    return user


# =========================================================
# ADMIN STATS
# =========================================================

@app.route("/api/admin/stats")
def admin_stats():

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM cases")
            cases = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM items")
            items = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM inventory")
            inventory = cur.fetchone()[0]

    return jsonify({
        "users": users,
        "cases": cases,
        "items": items,
        "inventory": inventory
    })


# =========================================================
# ADMIN CASES
# =========================================================

@app.route("/api/admin/cases")
def admin_cases():

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image,
                    active
                FROM cases
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price_coins": row[3],
            "price_stars": row[4],
            "image": row[5],
            "active": row[6]
        }
        for row in rows
    ])


@app.route("/api/admin/cases", methods=["POST"])
def admin_create_case():

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    data = request.get_json(silent=True) or {}

    name = data.get("name")

    if not name:
        return jsonify({
            "error": "Название кейса обязательно"
        }), 400

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO cases
                (
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image,
                    active
                )
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (
                name,
                data.get("description", ""),
                int(data.get("price_coins", 0)),
                int(data.get("price_stars", 0)),
                data.get("image", "")
            ))

            case_id = cur.fetchone()[0]

        conn.commit()

    return jsonify({
        "success": True,
        "id": case_id
    })


@app.route(
    "/api/admin/cases/<int:case_id>/disable",
    methods=["POST"]
)
def admin_disable_case(case_id):

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                UPDATE cases
                SET active = FALSE
                WHERE id = %s
            """, (
                case_id,
            ))

        conn.commit()

    return jsonify({
        "success": True
    })


# =========================================================
# ADMIN ITEMS
# =========================================================

@app.route("/api/admin/items")
def admin_items():

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    description,
                    rarity,
                    sell_price,
                    image
                FROM items
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "rarity": row[3],
            "sell_price": row[4],
            "image": row[5]
        }
        for row in rows
    ])


@app.route("/api/admin/items", methods=["POST"])
def admin_create_item():

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    data = request.get_json(silent=True) or {}

    name = data.get("name")

    if not name:
        return jsonify({
            "error": "Название предмета обязательно"
        }), 400

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO items
                (
                    name,
                    description,
                    rarity,
                    sell_price,
                    image
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name,
                data.get("description", ""),
                data.get("rarity", "common"),
                int(data.get("sell_price", 0)),
                data.get("image", "")
            ))

            item_id = cur.fetchone()[0]

        conn.commit()

    return jsonify({
        "success": True,
        "id": item_id
    })


# =========================================================
# ADMIN CASE ITEMS
# =========================================================

@app.route("/api/admin/case-items", methods=["POST"])
def admin_add_case_item():

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    data = request.get_json(silent=True) or {}

    case_id = data.get("case_id")
    item_id = data.get("item_id")
    drop_chance = data.get("drop_chance", 1)

    if not case_id or not item_id:
        return jsonify({
            "error": "case_id и item_id обязательны"
        }), 400

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO case_items
                (
                    case_id,
                    item_id,
                    drop_chance
                )
                VALUES (%s, %s, %s)
            """, (
                int(case_id),
                int(item_id),
                float(drop_chance)
            ))

        conn.commit()

    return jsonify({
        "success": True
    })


@app.route("/api/admin/cases/<int:case_id>/items")
def admin_case_items(case_id):

    if not require_admin():
        return jsonify({
            "error": "Forbidden"
        }), 403

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    ci.id,
                    ci.item_id,
                    i.name,
                    i.rarity,
                    ci.drop_chance
                FROM case_items ci
                JOIN items i
                    ON i.id = ci.item_id
                WHERE ci.case_id = %s
                ORDER BY ci.id
            """, (
                case_id,
            ))

            rows = cur.fetchall()

    return jsonify([
        {
            "id": row[0],
            "item_id": row[1],
            "name": row[2],
            "rarity": row[3],
            "drop_chance": row[4]
        }
        for row in rows
    ])


# =========================================================
# TELEGRAM BOT
# =========================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()


def main_keyboard(user_id):

    buttons = [
        [
            InlineKeyboardButton(
                text="🎁 Открыть VLDST",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                text="⚙️ Админ-панель",
                web_app=WebAppInfo(url=ADMIN_URL)
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(Command("start"))
async def start_command(message: types.Message):

    args = message.text.split(maxsplit=1)

    referral_code = None

    if len(args) > 1:
        referral_code = args[1]

    user = get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        referral_code
    )

    name = message.from_user.first_name or "Игрок"

    text = (
        f"🌌 <b>VLDST</b>\n\n"
        f"Добро пожаловать, <b>{name}</b>!\n\n"
        f"🪙 Coins: <b>{user['coins']}</b>\n"
        f"⭐ Stars: <b>{user['stars']}</b>\n"
        f"🏆 Уровень: <b>{user['level']}</b>\n"
        f"⚡ XP: <b>{user['xp']}</b>\n\n"
        f"🎁 Открывай кейсы и получай редкие предметы!"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard(message.from_user.id)
    )


@dp.message(Command("admin"))
async def admin_command(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ Открыть админ-панель",
                    web_app=WebAppInfo(url=ADMIN_URL)
                )
            ]
        ]
    )

    await message.answer(
        "⚙️ <b>Панель администратора VLDST</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================================================
# FLASK SERVER
# =========================================================

def run_flask():
    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# =========================================================
# BOT
# =========================================================

async def run_bot():

    init_db()

    print("VLDST bot started")

    await dp.start_polling(bot)


# =========================================================
# START
# =========================================================

def main():

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
