import os
import asyncio
import hashlib
import hmac
import json
import random
import html
import urllib.request
import urllib.parse
import time

from urllib.parse import parse_qsl
from threading import Thread

import psycopg
from flask import Flask, send_from_directory, request, jsonify

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    Message,
    PreCheckoutQuery,
)

from dotenv import load_dotenv


# ============================================================
# ENV
# ============================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "6038067496"
    )
)

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


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# CASES
# ============================================================

CASES = {
    2: ("VLDST CORE", 1000, 15, "core"),
    3: ("VLDST PULSE", 5000, 25, "pulse"),
    4: ("VLDST AURA", 15000, 50, "aura"),
    5: ("VLDST VOID", 30000, 75, "void"),
    6: ("VLDST OVERDRIVE", 60000, 100, "overdrive"),
    7: ("VLDST RIFT", 150000, 110, "rift"),
}


CASE_ITEMS = {
    2: list(range(6, 14)),
    3: list(range(14, 22)),
    4: list(range(22, 31)),
    5: list(range(31, 39)),
    6: list(range(39, 47)),
    7: list(range(47, 55)),
}


# ============================================================
# ITEMS
# ============================================================

ITEM_DATA = {
    6: ("Core Fragment", "COMMON", 250),
    7: ("Energy Cell", "COMMON", 300),
    8: ("Steel Chip", "COMMON", 350),
    9: ("Blue Core", "RARE", 700),
    10: ("Power Cell", "RARE", 850),
    11: ("Core Crystal", "EPIC", 1500),
    12: ("VLDST Blade", "LEGENDARY", 3500),
    13: ("CORE Overlord", "MYTHIC", 8000),

    14: ("Pulse Battery", "COMMON", 1000),
    15: ("Green Energy", "COMMON", 1200),
    16: ("Pulse Chip", "COMMON", 1400),
    17: ("Pulse Core", "RARE", 2500),
    18: ("Neon Crystal", "RARE", 3000),
    19: ("Pulse Reactor", "EPIC", 5500),
    20: ("Pulse Gun", "LEGENDARY", 12000),
    21: ("PULSE TITAN", "MYTHIC", 30000),

    22: ("Aura Shard", "COMMON", 3000),
    23: ("Blue Gem", "COMMON", 3500),
    24: ("Aura Crystal", "COMMON", 6000),
    25: ("Aura Crystal RARE", "RARE", 6000),
    26: ("Sky Core", "RARE", 7500),
    27: ("Aura Reactor", "EPIC", 12000),
    28: ("AURA Shield", "EPIC", 15000),
    29: ("AURA Blade", "LEGENDARY", 30000),
    30: ("AURA Phantom", "MYTHIC", 75000),

    31: ("Void Fragment", "COMMON", 6000),
    32: ("Dark Energy", "COMMON", 7000),
    33: ("Void Crystal", "RARE", 12000),
    34: ("Shadow Core", "RARE", 15000),
    35: ("Void Reactor", "EPIC", 25000),
    36: ("Void Shield", "EPIC", 30000),
    37: ("Void Reaper", "LEGENDARY", 60000),
    38: ("VOID KING", "MYTHIC", 150000),

    39: ("Overdrive Cell", "COMMON", 12000),
    40: ("Heat Core", "COMMON", 14000),
    41: ("Overdrive Crystal", "RARE", 25000),
    42: ("Turbo Core", "RARE", 33000),
    43: ("Overdrive Reactor", "EPIC", 50000),
    44: ("Overdrive Gun", "EPIC", 65000),
    45: ("OVERDRIVE X", "LEGENDARY", 120000),
    46: ("OVERDRIVE GOD", "MYTHIC", 280000),

    47: ("Rift Shard", "COMMON", 15000),
    48: ("Rift Energy", "COMMON", 18000),
    49: ("Rift Crystal", "RARE", 30000),
    50: ("Rift Core", "RARE", 40000),
    51: ("Rift Reactor", "EPIC", 65000),
    52: ("Rift Blaster", "EPIC", 90000),
    53: ("Rift Reaper", "LEGENDARY", 180000),
    54: ("VLDST RIFT GOD", "MYTHIC", 500000),
}


WEIGHTS = {
    "COMMON": 15.0,
    "RARE": 10.0,
    "EPIC": 7.5,
    "LEGENDARY": 4.0,
    "MYTHIC": 1.0,
}


# ============================================================
# STARS PRODUCTS
# ============================================================

STAR_PRODUCTS = {
    "stars_50": (
        50,
        50,
        "50 Telegram Stars"
    ),

    "stars_100": (
        100,
        100,
        "100 Telegram Stars"
    ),

    "stars_250": (
        250,
        250,
        "250 Telegram Stars"
    ),

    "stars_500": (
        500,
        500,
        "500 Telegram Stars"
    ),
}


STORE_PRODUCTS = {
    "premium_7": (
        "PREMIUM 7 DAYS",
        "premium",
        100,
        7,
        "Premium статус на 7 дней"
    ),

    "premium_30": (
        "PREMIUM 30 DAYS",
        "premium",
        300,
        30,
        "Premium статус на 30 дней"
    ),

    "boost_xp": (
        "XP BOOST",
        "xp_boost",
        75,
        24,
        "2x XP на 24 часа"
    ),

    "boost_coins": (
        "COIN BOOST",
        "coin_boost",
        75,
        24,
        "2x продажа предметов на 24 часа"
    ),

    "lucky": (
        "LUCKY BOOST",
        "lucky",
        125,
        24,
        "+50% эффективного веса дропа"
    ),
}


# ============================================================
# DATABASE
# ============================================================

def db():
    return psycopg.connect(DATABASE_URL)


def init_database():

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
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
                    banned BOOLEAN NOT NULL DEFAULT FALSE,
                    premium_until TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS cases(
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    price_coins BIGINT NOT NULL DEFAULT 0,
                    price_stars INTEGER NOT NULL DEFAULT 0,
                    image_url TEXT,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS items(
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    rarity TEXT NOT NULL,
                    sell_price BIGINT NOT NULL DEFAULT 0,
                    image_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS case_items(
                    id BIGSERIAL PRIMARY KEY,
                    case_id BIGINT REFERENCES cases(id)
                        ON DELETE CASCADE,
                    item_id BIGINT REFERENCES items(id)
                        ON DELETE CASCADE,
                    drop_chance NUMERIC(10,5) NOT NULL,
                    UNIQUE(case_id,item_id)
                )
            """)

            c.execute("""
                DELETE FROM case_items a
                USING case_items b
                WHERE a.id > b.id
                AND a.case_id = b.case_id
                AND a.item_id = b.item_id
            """)

            c.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                case_items_case_item_uq
                ON case_items(case_id,item_id)
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS inventory(
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT
                        REFERENCES users(telegram_id)
                        ON DELETE CASCADE,
                    item_id BIGINT
                        REFERENCES items(id),
                    obtained_from TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS transactions(
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    type TEXT NOT NULL,
                    amount BIGINT NOT NULL DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS tasks(
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    reward_coins BIGINT DEFAULT 0,
                    reward_stars INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT TRUE
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS task_claims(
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT
                        REFERENCES users(telegram_id)
                        ON DELETE CASCADE,
                    task_id BIGINT
                        REFERENCES tasks(id)
                        ON DELETE CASCADE,
                    claimed_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(telegram_id,task_id)
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts(
                    id BIGSERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    sent INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS user_boosts(
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT
                        REFERENCES users(telegram_id)
                        ON DELETE CASCADE,
                    boost_type TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    UNIQUE(telegram_id,boost_type)
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS daily_claims(
                    telegram_id BIGINT PRIMARY KEY
                        REFERENCES users(telegram_id)
                        ON DELETE CASCADE,
                    claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS mini_game_scores(
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT
                        REFERENCES users(telegram_id)
                        ON DELETE CASCADE,
                    score INTEGER NOT NULL,
                    coins BIGINT NOT NULL DEFAULT 0,
                    played_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            c.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS premium_until TIMESTAMPTZ
            """)

            # CASES

            for cid, (
                name,
                price_coins,
                price_stars,
                key
            ) in CASES.items():

                c.execute("""
                    INSERT INTO cases(
                        id,
                        name,
                        description,
                        price_coins,
                        price_stars,
                        image_url,
                        active
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,TRUE)

                    ON CONFLICT(id)
                    DO UPDATE SET
                        name=EXCLUDED.name,
                        description=EXCLUDED.description,
                        price_coins=EXCLUDED.price_coins,
                        price_stars=EXCLUDED.price_stars,
                        image_url=EXCLUDED.image_url,
                        active=TRUE
                """, (
                    cid,
                    name,
                    f"{name} — эксклюзивный кейс",
                    price_coins,
                    price_stars,
                    f"/webapp/assets/cases/{key}.svg"
                ))

            # ITEMS

            for iid, (
                name,
                rarity,
                sell
            ) in ITEM_DATA.items():

                c.execute("""
                    INSERT INTO items(
                        id,
                        name,
                        description,
                        rarity,
                        sell_price,
                        image_url
                    )
                    VALUES(%s,%s,%s,%s,%s,%s)

                    ON CONFLICT(id)
                    DO UPDATE SET
                        name=EXCLUDED.name,
                        rarity=EXCLUDED.rarity,
                        sell_price=EXCLUDED.sell_price,
                        image_url=EXCLUDED.image_url
                """, (
                    iid,
                    name,
                    f"Предмет {name} из VLDST CASE",
                    rarity,
                    sell,
                    f"/webapp/assets/items/{iid}.svg"
                ))

            # CASE ITEMS

            for cid, ids in CASE_ITEMS.items():

                for iid in ids:

                    rarity = ITEM_DATA[iid][1]

                    c.execute("""
                        INSERT INTO case_items(
                            case_id,
                            item_id,
                            drop_chance
                        )
                        VALUES(%s,%s,%s)

                        ON CONFLICT(case_id,item_id)
                        DO UPDATE SET
                            drop_chance=EXCLUDED.drop_chance
                    """, (
                        cid,
                        iid,
                        WEIGHTS[rarity]
                    ))

            # DEFAULT TASK

            c.execute("""
                INSERT INTO tasks(
                    title,
                    description,
                    reward_coins,
                    active
                )

                SELECT
                    'Ежедневный бонус',
                    'Забери ежедневную награду',
                    1000,
                    TRUE

                WHERE NOT EXISTS(
                    SELECT 1 FROM tasks
                )
            """)

            conn.commit()


# ============================================================
# TELEGRAM AUTH
# ============================================================

def verify_telegram_init_data(data):

    if not data:
        return None

    try:

        parsed = dict(
            parse_qsl(
                data,
                keep_blank_values=True
            )
        )

        received_hash = parsed.pop(
            "hash",
            None
        )

        if not received_hash:
            return None

        check_string = "\n".join(
            f"{key}={value}"
            for key, value
            in sorted(parsed.items())
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

        if not parsed.get("user"):
            return None

        return json.loads(
            parsed["user"]
        )

    except Exception as error:

        print(
            "Telegram auth error:",
            error
        )

        return None


def tg_user():

    return verify_telegram_init_data(
        request.headers.get(
            "X-Telegram-Init-Data",
            ""
        )
    )


def is_admin():

    user = tg_user()

    return bool(
        user
        and int(user.get("id", 0)) == ADMIN_ID
    )


# ============================================================
# USER
# ============================================================

def ensure_user(user, ref=None):

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                INSERT INTO users(
                    telegram_id,
                    username,
                    first_name,
                    referral_code
                )

                VALUES(
                    %s,
                    %s,
                    %s,
                    %s
                )

                ON CONFLICT(telegram_id)
                DO UPDATE SET
                    username=EXCLUDED.username,
                    first_name=EXCLUDED.first_name

                RETURNING
                    telegram_id,
                    coins,
                    stars,
                    level,
                    xp,
                    referred_by,
                    banned
            """, (
                telegram_id,
                user.get("username"),
                user.get("first_name") or "Игрок",
                f"VLDST{telegram_id}"
            ))

            row = c.fetchone()

            # Referral

            if (
                ref
                and ref != telegram_id
                and row[5] is None
            ):

                c.execute("""
                    SELECT telegram_id
                    FROM users
                    WHERE telegram_id=%s
                """, (ref,))

                referrer = c.fetchone()

                if referrer:

                    c.execute("""
                        UPDATE users
                        SET
                            referred_by=%s,
                            coins=coins+500
                        WHERE telegram_id=%s
                        AND referred_by IS NULL
                    """, (
                        ref,
                        telegram_id
                    ))

                    if c.rowcount:

                        c.execute("""
                            UPDATE users
                            SET coins=coins+500
                            WHERE telegram_id=%s
                        """, (ref,))

            conn.commit()

    return row


# ============================================================
# BOOST
# ============================================================

def active_boost(
    telegram_id,
    boost_type
):

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM user_boosts
                    WHERE telegram_id=%s
                    AND boost_type=%s
                    AND expires_at>NOW()
                )
            """, (
                telegram_id,
                boost_type
            ))

            row = c.fetchone()

    return bool(
        row and row[0]
    )


# ============================================================
# SELECT ITEM
# ============================================================

def select_item(
    case_id,
    telegram_id=None
):

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    i.id,
                    i.name,
                    i.description,
                    i.rarity,
                    i.sell_price,
                    i.image_url,
                    ci.drop_chance

                FROM case_items ci

                JOIN items i
                ON i.id=ci.item_id

                WHERE ci.case_id=%s
            """, (case_id,))

            rows = c.fetchall()

    if not rows:
        return None

    multiplier = (
        1.5
        if telegram_id
        and active_boost(
            telegram_id,
            "lucky"
        )
        else 1
    )

    total = sum(
        float(row[6]) * multiplier
        for row in rows
    )

    roll = random.uniform(
        0,
        total
    )

    current = 0

    for row in rows:

        current += (
            float(row[6])
            * multiplier
        )

        if roll <= current:
            return row

    return rows[-1]


# ============================================================
# XP
# ============================================================

def xp_gain(
    telegram_id,
    amount
):

    if active_boost(
        telegram_id,
        "xp_boost"
    ):
        amount *= 2

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                UPDATE users

                SET
                    xp=xp+%s,
                    level=GREATEST(
                        1,
                        FLOOR(
                            (xp+%s)/100
                        )+1
                    )::INTEGER

                WHERE telegram_id=%s
            """, (
                amount,
                amount,
                telegram_id
            ))

            conn.commit()


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def home():

    return "VLDST CASE Backend is running!"


@app.get("/health")
def health():

    return {
        "status": "ok",
        "project": "VLDST CASE",
        "version": "ultimate-mobile"
    }


@app.route("/webapp/<path:filename>")
def webapp(filename):

    return send_from_directory(
        "webapp",
        filename
    )


# ============================================================
# USER API
# ============================================================

@app.get("/api/user")
@app.get("/api/me")
def api_user():

    user = tg_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    coins,
                    stars,
                    level,
                    xp,
                    referral_code,
                    banned,
                    premium_until

                FROM users

                WHERE telegram_id=%s
            """, (telegram_id,))

            row = c.fetchone()

    if not row:

        ensure_user(user)

        return api_user()

    return {
        "telegram_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "coins": row[3],
        "stars": row[4],
        "level": row[5],
        "xp": row[6],
        "referral_code": row[7],
        "banned": row[8],
        "premium_until": (
            row[9].isoformat()
            if row[9]
            else None
        )
    }


# ============================================================
# CASES API
# ============================================================

@app.get("/api/cases")
def api_cases():

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    id,
                    name,
                    description,
                    price_coins,
                    price_stars,
                    image_url

                FROM cases

                WHERE active=TRUE

                ORDER BY id
            """)

            rows = c.fetchall()

    return {
        "cases": [
            {
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "price_coins": r[3],
                "price_stars": r[4],
                "image_url": r[5]
            }
            for r in rows
        ]
    }


@app.get("/api/cases/<int:cid>/items")
def case_items(cid):

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    i.id,
                    i.name,
                    i.description,
                    i.rarity,
                    i.sell_price,
                    i.image_url,
                    ci.drop_chance

                FROM case_items ci

                JOIN items i
                ON i.id=ci.item_id

                WHERE ci.case_id=%s

                ORDER BY
                    ci.drop_chance DESC,
                    i.id
            """, (cid,))

            rows = c.fetchall()

    return {
        "items": [
            {
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "rarity": r[3],
                "sell_price": r[4],
                "image_url": r[5],
                "drop_chance": float(r[6])
            }
            for r in rows
        ]
    }


# ============================================================
# INVENTORY
# ============================================================

@app.get("/api/inventory")
def inventory():

    user = tg_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    inv.id,
                    i.id,
                    i.name,
                    i.description,
                    i.rarity,
                    i.sell_price,
                    i.image_url,
                    inv.obtained_from,
                    inv.created_at

                FROM inventory inv

                JOIN items i
                ON i.id=inv.item_id

                WHERE inv.telegram_id=%s

                ORDER BY inv.created_at DESC
            """, (telegram_id,))

            rows = c.fetchall()

    return {
        "inventory": [
            {
                "inventory_id": r[0],
                "item_id": r[1],
                "name": r[2],
                "description": r[3],
                "rarity": r[4],
                "sell_price": r[5],
                "image_url": r[6],
                "obtained_from": r[7],
                "created_at": r[8].isoformat()
            }
            for r in rows
        ]
    }


@app.post("/api/inventory/<int:iid>/sell")
def sell(iid):

    user = tg_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    i.name,
                    i.sell_price

                FROM inventory inv

                JOIN items i
                ON i.id=inv.item_id

                WHERE inv.id=%s
                AND inv.telegram_id=%s

                FOR UPDATE
            """, (
                iid,
                telegram_id
            ))

            item = c.fetchone()

            if not item:

                return {
                    "error": "not_found"
                }, 404

            value = int(
                item[1]
            )

            if active_boost(
                telegram_id,
                "coin_boost"
            ):
                value *= 2

            c.execute("""
                DELETE FROM inventory

                WHERE id=%s
                AND telegram_id=%s
            """, (
                iid,
                telegram_id
            ))

            c.execute("""
                UPDATE users

                SET coins=coins+%s

                WHERE telegram_id=%s

                RETURNING coins
            """, (
                value,
                telegram_id
            ))

            coins = c.fetchone()[0]

            conn.commit()

    return {
        "success": True,
        "coins": coins,
        "sold_for": value
    }


# ============================================================
# OPEN CASE
# ============================================================

@app.post("/api/cases/<int:cid>/open")
def open_case(cid):

    user = tg_user()

    if not user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    coins,
                    banned

                FROM users

                WHERE telegram_id=%s

                FOR UPDATE
            """, (telegram_id,))

            user_row = c.fetchone()

            if not user_row:

                return {
                    "error": "user_not_found"
                }, 404

            if user_row[1]:

                return {
                    "error": "banned"
                }, 403

            c.execute("""
                SELECT
                    name,
                    price_coins

                FROM cases

                WHERE id=%s
                AND active=TRUE
            """, (cid,))

            case = c.fetchone()

            if not case:

                return {
                    "error": "case_not_found"
                }, 404

            if user_row[0] < case[1]:

                return {
                    "error": "not_enough_coins"
                }, 400

            item = select_item(
                cid,
                telegram_id
            )

            if not item:

                return {
                    "error": "case_has_no_items"
                }, 500

            c.execute("""
                UPDATE users

                SET coins=coins-%s

                WHERE telegram_id=%s

                RETURNING coins
            """, (
                case[1],
                telegram_id
            ))

            coins = c.fetchone()[0]

            c.execute("""
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
            """, (
                telegram_id,
                item[0],
                f"case:{cid}"
            ))

            c.execute("""
                INSERT INTO transactions(
                    telegram_id,
                    type,
                    amount,
                    description
                )

                VALUES(
                    %s,
                    'case_open',
                    %s,
                    %s
                )
            """, (
                telegram_id,
                -case[1],
                f"Открытие кейса {cid}"
            ))

            conn.commit()

    xp_gain(
        telegram_id,
        10
    )

    return {
        "success": True,
        "coins": coins,
        "item": {
            "id": item[0],
            "name": item[1],
            "description": item[2],
            "rarity": item[3],
            "sell_price": item[4],
            "image_url": item[5]
        }
    }


# ============================================================
# TELEGRAM API
# ============================================================

def telegram_api(
    method,
    payload
):

    data = urllib.parse.urlencode(
        payload
    ).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=data
    )

    with urllib.request.urlopen(
        req,
        timeout=20
    ) as response:

        return json.loads(
            response.read().decode()
        )


# ============================================================
# STARS INVOICE
# ============================================================

@app.post("/api/stars/invoice")
def stars_invoice():

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    kind = data.get(
        "kind",
        "balance"
    )

    telegram_id = int(
        user["id"]
    )

    # Balance

    if kind == "balance":

        product = data.get(
            "product",
            "stars_100"
        )

        if product not in STAR_PRODUCTS:

            return {
                "error": "bad_product"
            }, 400

        stars, _, title = (
            STAR_PRODUCTS[product]
        )

        payload = (
            f"balance:"
            f"{telegram_id}:"
            f"{stars}:"
            f"{int(time.time())}"
        )

    # Case

    elif kind == "case":

        cid = int(
            data.get(
                "case_id",
                0
            )
        )

        if cid not in CASES:

            return {
                "error": "bad_case"
            }, 400

        title = CASES[cid][0]
        stars = CASES[cid][2]

        payload = (
            f"case:"
            f"{telegram_id}:"
            f"{cid}:"
            f"{int(time.time())}"
        )

    # Store

    elif kind == "store":

        product = data.get(
            "product"
        )

        if product not in STORE_PRODUCTS:

            return {
                "error": "bad_product"
            }, 400

        (
            title,
            boost_type,
            stars,
            duration,
            description
        ) = STORE_PRODUCTS[product]

        payload = (
            f"store:"
            f"{telegram_id}:"
            f"{product}:"
            f"{int(time.time())}"
        )

    else:

        return {
            "error": "bad_kind"
        }, 400

    result = telegram_api(
        "createInvoiceLink",
        {
            "title": title,
            "description": (
                "VLDST CASE • "
                + title
            ),
            "payload": payload,
            "currency": "XTR",
            "prices": json.dumps([
                {
                    "label": title,
                    "amount": stars
                }
            ])
        }
    )

    if not result.get("ok"):

        print(
            "Telegram invoice error:",
            result
        )

        return {
            "error": "telegram_invoice_error"
        }, 500

    return {
        "invoice_url": result["result"]
    }


# ============================================================
# SHOP
# ============================================================

@app.get("/api/shop")
def shop():

    return {
        "balance_products": [
            {
                "id": key,
                "stars": value[0],
                "title": value[2]
            }
            for key, value
            in STAR_PRODUCTS.items()
        ],

        "store_products": [
            {
                "id": key,
                "title": value[0],
                "type": value[1],
                "stars": value[2],
                "duration": value[3],
                "description": value[4]
            }
            for key, value
            in STORE_PRODUCTS.items()
        ]
    }


# ============================================================
# BOOSTS
# ============================================================

@app.get("/api/boosts")
def boosts():

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    boost_type,
                    expires_at

                FROM user_boosts

                WHERE telegram_id=%s
                AND expires_at>NOW()

                ORDER BY expires_at
            """, (telegram_id,))

            rows = c.fetchall()

    return {
        "boosts": [
            {
                "type": r[0],
                "expires_at": r[1].isoformat()
            }
            for r in rows
        ]
    }


# ============================================================
# REFERRALS
# ============================================================

@app.get("/api/referrals")
def referrals():

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE referred_by=%s
            """, (telegram_id,))

            count = c.fetchone()[0]

            c.execute("""
                SELECT
                    COALESCE(
                        COUNT(*) * 500,
                        0
                    )

                FROM users

                WHERE referred_by=%s
            """, (telegram_id,))

            earned = c.fetchone()[0]

    return {
        "referral_link": (
            f"https://t.me/"
            f"{BOT_USERNAME}"
            f"?start=ref_{telegram_id}"
        ),
        "count": count,
        "earned": earned
    }


# ============================================================
# LEADERBOARD
# ============================================================

@app.get("/api/leaderboard")
def leaderboard():

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    username,
                    first_name,
                    level,
                    xp,
                    coins

                FROM users

                WHERE banned=FALSE

                ORDER BY
                    xp DESC,
                    coins DESC

                LIMIT 50
            """)

            rows = c.fetchall()

    return {
        "leaderboard": [
            {
                "username": r[0],
                "first_name": r[1],
                "level": r[2],
                "xp": r[3],
                "coins": r[4]
            }
            for r in rows
        ]
    }


# ============================================================
# TASKS
# ============================================================

@app.get("/api/tasks")
def tasks():

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    t.id,
                    t.title,
                    t.description,
                    t.reward_coins,
                    t.reward_stars,

                    EXISTS(
                        SELECT 1

                        FROM task_claims x

                        WHERE x.task_id=t.id
                        AND x.telegram_id=%s
                    )

                FROM tasks t

                WHERE t.active=TRUE

                ORDER BY t.id
            """, (telegram_id,))

            rows = c.fetchall()

    return {
        "tasks": [
            {
                "id": r[0],
                "title": r[1],
                "description": r[2],
                "reward_coins": r[3],
                "reward_stars": r[4],
                "claimed": r[5]
            }
            for r in rows
        ]
    }


@app.post("/api/tasks/<int:task_id>/claim")
def claim_task(task_id):

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    reward_coins,
                    reward_stars

                FROM tasks

                WHERE id=%s
                AND active=TRUE
            """, (task_id,))

            task = c.fetchone()

            if not task:

                return {
                    "error": "task_not_found"
                }, 404

            c.execute("""
                SELECT 1

                FROM task_claims

                WHERE telegram_id=%s
                AND task_id=%s
            """, (
                telegram_id,
                task_id
            ))

            if c.fetchone():

                return {
                    "error": "already_claimed"
                }, 400

            c.execute("""
                INSERT INTO task_claims(
                    telegram_id,
                    task_id
                )

                VALUES(%s,%s)
            """, (
                telegram_id,
                task_id
            ))

            c.execute("""
                UPDATE users

                SET
                    coins=coins+%s,
                    stars=stars+%s

                WHERE telegram_id=%s

                RETURNING coins,stars
            """, (
                task[0],
                task[1],
                telegram_id
            ))

            result = c.fetchone()

            conn.commit()

    return {
        "success": True,
        "coins": result[0],
        "stars": result[1]
    }


# ============================================================
# DAILY
# ============================================================

@app.post("/api/daily")
def daily():

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM daily_claims
                    WHERE telegram_id=%s
                    AND claimed_at::date=CURRENT_DATE
                )
            """, (telegram_id,))

            already = c.fetchone()[0]

            if already:

                return {
                    "error": "already_claimed"
                }, 400

            reward = 1000

            c.execute("""
                INSERT INTO daily_claims(
                    telegram_id,
                    claimed_at
                )

                VALUES(
                    %s,
                    NOW()
                )

                ON CONFLICT(telegram_id)
                DO UPDATE SET
                    claimed_at=NOW()
            """, (telegram_id,))

            c.execute("""
                UPDATE users

                SET coins=coins+%s

                WHERE telegram_id=%s

                RETURNING coins
            """, (
                reward,
                telegram_id
            ))

            coins = c.fetchone()[0]

            conn.commit()

    return {
        "success": True,
        "coins": coins,
        "reward": reward
    }


# ============================================================
# MINI GAME
# ============================================================

@app.post("/api/minigame/play")
def minigame():

    user = tg_user()

    if not user:

        return {
            "error": "unauthorized"
        }, 401

    telegram_id = int(
        user["id"]
    )

    score = random.randint(
        10,
        100
    )

    reward = score * 10

    if active_boost(
        telegram_id,
        "coin_boost"
    ):
        reward *= 2

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                INSERT INTO mini_game_scores(
                    telegram_id,
                    score,
                    coins
                )

                VALUES(%s,%s,%s)
            """, (
                telegram_id,
                score,
                reward
            ))

            c.execute("""
                UPDATE users

                SET coins=coins+%s

                WHERE telegram_id=%s

                RETURNING coins
            """, (
                reward,
                telegram_id
            ))

            coins = c.fetchone()[0]

            conn.commit()

    xp_gain(
        telegram_id,
        5
    )

    return {
        "success": True,
        "score": score,
        "reward": reward,
        "coins": coins
    }


# ============================================================
# ADMIN CHECK
# ============================================================

@app.get("/api/admin/check")
def admin_check():

    return {
        "admin": is_admin()
    }


# ============================================================
# ADMIN STATS
# ============================================================

@app.get("/api/admin/stats")
def admin_stats():

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    with db() as conn:

        with conn.cursor() as c:

            output = {}

            tables = (
                "users",
                "cases",
                "items",
                "inventory",
                "transactions",
                "broadcasts",
                "user_boosts",
                "mini_game_scores"
            )

            for table in tables:

                c.execute(
                    f"SELECT COUNT(*) FROM {table}"
                )

                output[table] = c.fetchone()[0]

            c.execute("""
                SELECT
                    COALESCE(SUM(coins),0),
                    COALESCE(SUM(stars),0)

                FROM users
            """)

            output["coins"], output["stars"] = (
                c.fetchone()
            )

            c.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE banned=TRUE
            """)

            output["banned"] = (
                c.fetchone()[0]
            )

    return output


# ============================================================
# ADMIN USERS
# ============================================================

@app.get("/api/admin/users")
def admin_users():

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    coins,
                    stars,
                    level,
                    xp,
                    banned,
                    premium_until

                FROM users

                ORDER BY created_at DESC

                LIMIT 500
            """)

            rows = c.fetchall()

    return {
        "users": [
            {
                "telegram_id": r[0],
                "username": r[1],
                "first_name": r[2],
                "coins": r[3],
                "stars": r[4],
                "level": r[5],
                "xp": r[6],
                "banned": r[7],
                "premium_until": (
                    r[8].isoformat()
                    if r[8]
                    else None
                )
            }
            for r in rows
        ]
    }


# ============================================================
# ADMIN BAN
# ============================================================

@app.post("/api/admin/user/<int:telegram_id>/ban")
def ban_user(telegram_id):

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    banned = bool(
        data.get(
            "banned",
            True
        )
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                UPDATE users

                SET banned=%s

                WHERE telegram_id=%s
            """, (
                banned,
                telegram_id
            ))

            conn.commit()

    return {
        "success": True,
        "banned": banned
    }


# ============================================================
# ADMIN GIVE COINS
# ============================================================

@app.post("/api/admin/give-coins")
def give_coins():

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

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

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                UPDATE users

                SET coins=coins+%s

                WHERE telegram_id=%s

                RETURNING coins
            """, (
                amount,
                telegram_id
            ))

            row = c.fetchone()

            if not row:

                return {
                    "error": "user_not_found"
                }, 404

            conn.commit()

    return {
        "success": True,
        "coins": row[0]
    }


# ============================================================
# ADMIN GIVE STARS
# ============================================================

@app.post("/api/admin/give-stars")
def give_stars():

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

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

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                UPDATE users

                SET stars=stars+%s

                WHERE telegram_id=%s

                RETURNING stars
            """, (
                amount,
                telegram_id
            ))

            row = c.fetchone()

            if not row:

                return {
                    "error": "user_not_found"
                }, 404

            conn.commit()

    return {
        "success": True,
        "stars": row[0]
    }


# ============================================================
# ADMIN BROADCAST
# ============================================================

@app.post("/api/admin/broadcast")
def broadcast():

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    text = str(
        data.get(
            "text",
            ""
        )
    ).strip()

    if not text:

        return {
            "error": "text_required"
        }, 400

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT telegram_id
                FROM users
                WHERE banned=FALSE
            """)

            ids = [
                row[0]
                for row in c.fetchall()
            ]

    sent = 0
    failed = 0

    for telegram_id in ids:

        try:

            telegram_api(
                "sendMessage",
                {
                    "chat_id": telegram_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )

            sent += 1

        except Exception:

            failed += 1

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                INSERT INTO broadcasts(
                    text,
                    sent,
                    failed
                )

                VALUES(
                    %s,
                    %s,
                    %s
                )
            """, (
                text,
                sent,
                failed
            ))

            conn.commit()

    return {
        "success": True,
        "sent": sent,
        "failed": failed
    }


# ============================================================
# ADMIN CASES
# ============================================================

@app.get("/api/admin/cases")
def admin_cases():

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                SELECT
                    id,
                    name,
                    price_coins,
                    price_stars,
                    image_url,
                    active

                FROM cases

                ORDER BY id
            """)

            rows = c.fetchall()

    return {
        "cases": [
            {
                "id": r[0],
                "name": r[1],
                "price_coins": r[2],
                "price_stars": r[3],
                "image_url": r[4],
                "active": r[5]
            }
            for r in rows
        ]
    }


@app.post("/api/admin/cases/<int:cid>/toggle")
def toggle_case(cid):

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                UPDATE cases

                SET active=NOT active

                WHERE id=%s

                RETURNING active
            """, (cid,))

            row = c.fetchone()

            conn.commit()

    return {
        "success": True,
        "active": (
            row[0]
            if row
            else None
        )
    }


# ============================================================
# ADMIN PREMIUM
# ============================================================

@app.post("/api/admin/user/<int:telegram_id>/premium")
def admin_premium(telegram_id):

    if not is_admin():

        return {
            "error": "forbidden"
        }, 403

    days = int(
        (
            request.get_json(
                silent=True
            )
            or {}
        ).get(
            "days",
            30
        )
    )

    with db() as conn:

        with conn.cursor() as c:

            c.execute("""
                UPDATE users

                SET premium_until=
                    GREATEST(
                        COALESCE(
                            premium_until,
                            NOW()
                        ),
                        NOW()
                    )
                    +(%s || ' days')::interval

                WHERE telegram_id=%s

                RETURNING premium_until
            """, (
                days,
                telegram_id
            ))

            row = c.fetchone()

            conn.commit()

    return {
        "success": bool(row),
        "premium_until": (
            row[0].isoformat()
            if row
            else None
        )
    }


# ============================================================
# PAYMENT SUCCESS
# ============================================================

async def payment_success(
    message: Message
):

    payment = (
        message.successful_payment
    )

    if not payment:
        return

    payload = (
        payment.invoice_payload
    )

    parts = payload.split(":")

    telegram_id = (
        message.from_user.id
    )

    # BALANCE

    if parts[0] == "balance":

        stars = int(
            parts[2]
        )

        with db() as conn:

            with conn.cursor() as c:

                c.execute("""
                    UPDATE users

                    SET stars=stars+%s

                    WHERE telegram_id=%s

                    RETURNING stars
                """, (
                    stars,
                    telegram_id
                ))

                row = c.fetchone()

                conn.commit()

        if row:

            await message.answer(
                f"⭐ <b>Оплата успешна!</b>\n\n"
                f"Зачислено: <b>{stars}</b> Stars\n"
                f"Баланс: <b>{row[0]}</b> ⭐",
                parse_mode="HTML"
            )

    # CASE WITH STARS

    elif parts[0] == "case":

        case_id = int(
            parts[2]
        )

        item = select_item(
            case_id,
            telegram_id
        )

        if not item:
            return

        with db() as conn:

            with conn.cursor() as c:

                c.execute("""
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
                """, (
                    telegram_id,
                    item[0],
                    f"stars_case:{case_id}"
                ))

                conn.commit()

        xp_gain(
            telegram_id,
            10
        )

        await message.answer(
            f"🎉 <b>Кейс открыт!</b>\n\n"
            f"💎 {html.escape(item[1])}\n"
            f"Редкость: <b>{item[3]}</b>\n"
            f"Продажа: 🪙 <b>{item[4]:,}</b>",
            parse_mode="HTML"
        )

    # STORE

    elif parts[0] == "store":

        product = parts[2]

        if product not in STORE_PRODUCTS:
            return

        (
            title,
            boost_type,
            stars,
            duration,
            description
        ) = STORE_PRODUCTS[product]

        with db() as conn:

            with conn.cursor() as c:

                if boost_type == "premium":

                    c.execute("""
                        UPDATE users

                        SET premium_until=
                            GREATEST(
                                COALESCE(
                                    premium_until,
                                    NOW()
                                ),
                                NOW()
                            )
                            +(%s || ' days')::interval

                        WHERE telegram_id=%s
                    """, (
                        duration,
                        telegram_id
                    ))

                else:

                    c.execute("""
                        INSERT INTO user_boosts(
                            telegram_id,
                            boost_type,
                            expires_at
                        )

                        VALUES(
                            %s,
                            %s,
                            NOW()
                            +(%s || ' hours')::interval
                        )

                        ON CONFLICT(
                            telegram_id,
                            boost_type
                        )

                        DO UPDATE SET
                            expires_at=
                                GREATEST(
                                    user_boosts.expires_at,
                                    NOW()
                                )
                                +(%s || ' hours')::interval
                    """, (
                        telegram_id,
                        boost_type,
                        duration,
                        duration
                    ))

                conn.commit()

        await message.answer(
            f"✨ <b>{html.escape(title)}</b>\n\n"
            f"Активировано!",
            parse_mode="HTML"
        )


# ============================================================
# BOT
# ============================================================

bot = Bot(
    TOKEN
)

dp = Dispatcher()


# ============================================================
# ADMIN COMMAND
# ============================================================

@dp.message(Command("admin"))
async def admin_cmd(
    message: Message
):

    if (
        not message.from_user
        or message.from_user.id != ADMIN_ID
    ):

        await message.answer(
            "⛔ Доступ запрещён."
        )

        return

    await message.answer(
        "🛠 <b>VLDST ADMIN</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚙️ Админ-панель",
                        web_app=WebAppInfo(
                            url=ADMIN_URL
                        )
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start(
    message: Message
):

    user = message.from_user

    if not user:
        return

    ref = None

    parts = (
        message.text.split(
            maxsplit=1
        )
        if message.text
        else []
    )

    if (
        len(parts) > 1
        and parts[1].startswith("ref_")
    ):

        try:

            ref = int(
                parts[1][4:]
            )

        except ValueError:

            ref = None

    row = ensure_user(
        {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name
        },
        ref
    )

    if row[6]:

        await message.answer(
            "⛔ Ваш аккаунт заблокирован."
        )

        return

    buttons = [
        [
            InlineKeyboardButton(
                text="🎁 Открыть VLDST CASE",
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

    await message.answer(
        f"🌌 <b>VLDST CASE</b>\n\n"
        f"Добро пожаловать, "
        f"<b>{html.escape(user.first_name or 'Игрок')}</b>!\n\n"
        f"🪙 Coins: <b>{row[1]:,}</b>\n"
        f"⭐ Stars: <b>{row[2]}</b>\n"
        f"🏆 Уровень: <b>{row[3]}</b>\n"
        f"⚡ XP: <b>{row[4]}</b>\n\n"
        f"Открывай кейсы и получай редкие предметы!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )


# ============================================================
# PRE CHECKOUT
# ============================================================

@dp.pre_checkout_query()
async def pre_checkout(
    query: PreCheckoutQuery
):

    await query.answer(
        ok=True
    )


# ============================================================
# PAYMENT
# ============================================================

@dp.message(
    F.successful_payment
)
async def success_payment(
    message: Message
):

    await payment_success(
        message
    )


# ============================================================
# WEB SERVER
# ============================================================

def run_web():

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "10000"
            )
        ),
        threaded=True
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    print(
        "VLDST CASE: запуск..."
    )

    init_database()

    print(
        "VLDST CASE: database ready"
    )

    Thread(
        target=run_web,
        daemon=True
    ).start()

    print(
        "VLDST CASE: web server started"
    )

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":

    asyncio.run(
        main()
)
