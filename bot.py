import os
import asyncio
import threading
import time
import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
import psycopg
from psycopg.rows import dict_row

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton,
    PreCheckoutQuery, LabeledPrice
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
BOT_USERNAME = os.getenv("BOT_USERNAME", "VLDST_CASE_BOT").strip().lstrip("@")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")
if not WEBAPP_URL.startswith("https://"):
    raise RuntimeError("WEBAPP_URL must start with https://")

for suffix in ("/webapp", "/admin"):
    if WEBAPP_URL.endswith(suffix):
        WEBAPP_URL = WEBAPP_URL[:-len(suffix)].rstrip("/")
        break

BASE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE, "webapp")
app = Flask(__name__)

BOT_LOOP = None
bot_instance = None


def db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)


def now():
    return datetime.now(timezone.utc)


def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users(
        id BIGSERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT NOT NULL DEFAULT 'Игрок',
        coins BIGINT NOT NULL DEFAULT 1000,
        stars BIGINT NOT NULL DEFAULT 0,
        xp BIGINT NOT NULL DEFAULT 0,
        level INT NOT NULL DEFAULT 1,
        premium_until TIMESTAMPTZ,
        banned BOOLEAN NOT NULL DEFAULT FALSE,
        referred_by BIGINT,
        daily_claimed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS cases(
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        image_url TEXT NOT NULL DEFAULT '',
        price_coins BIGINT NOT NULL DEFAULT 1000,
        price_stars INT NOT NULL DEFAULT 10,
        active BOOLEAN NOT NULL DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS items(
        id SERIAL PRIMARY KEY,
        case_id INT REFERENCES cases(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        rarity TEXT NOT NULL DEFAULT 'common',
        image_url TEXT NOT NULL DEFAULT '',
        sell_price BIGINT NOT NULL DEFAULT 100,
        weight NUMERIC NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS inventory(
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        item_id INT REFERENCES items(id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        sold_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS tasks(
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        reward_coins BIGINT NOT NULL DEFAULT 0,
        reward_stars INT NOT NULL DEFAULT 0,
        active BOOLEAN NOT NULL DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS task_claims(
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        task_id INT REFERENCES tasks(id) ON DELETE CASCADE,
        claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(user_id, task_id)
    );

    CREATE TABLE IF NOT EXISTS boosts(
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        type TEXT NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL
    );

    CREATE TABLE IF NOT EXISTS payments(
        id BIGSERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        payload TEXT UNIQUE NOT NULL,
        kind TEXT NOT NULL,
        product_id TEXT,
        amount INT NOT NULL,
        status TEXT NOT NULL DEFAULT 'created',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    with db() as con:
        with con.cursor() as cur:
            cur.execute(schema)

            cur.execute("SELECT COUNT(*) AS n FROM cases")
            if cur.fetchone()["n"] == 0:
                seed(con)

            cur.execute("SELECT COUNT(*) AS n FROM tasks")
            if cur.fetchone()["n"] == 0:
                cur.executemany(
                    """
                    INSERT INTO tasks(title,description,reward_coins,reward_stars)
                    VALUES(%s,%s,%s,%s)
                    """,
                    [
                        ("Первый вход", "Зайди в VLDST CASE.", 500, 0),
                        ("Собери 3 предмета", "Открывай кейсы.", 1500, 0),
                        ("Игрок дня", "Сыграй в VLDST RUSH.", 750, 0),
                    ],
                )
        con.commit()


def svg_data(title, subtitle, color, kind="item"):
    def esc(s):
        return (
            str(s).replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    title = esc(title)[:24]
    subtitle = esc(subtitle)[:20]

    center = f"""
      <circle cx="400" cy="315" r="142" fill="#080A12" stroke="{color}" stroke-width="8"/>
      <text x="400" y="300" text-anchor="middle" font-family="Arial,sans-serif"
            font-size="48" font-weight="900" fill="#fff">VLDST</text>
      <text x="400" y="352" text-anchor="middle" font-family="Arial,sans-serif"
            font-size="27" font-weight="900" fill="{color}">{title}</text>
    """

    if kind == "case":
        center = f"""
          <rect x="145" y="190" width="510" height="245" rx="48"
                fill="#0B0E19" stroke="{color}" stroke-width="10"/>
          <rect x="178" y="225" width="444" height="175" rx="30"
                fill="#14182A" stroke="{color}" stroke-opacity=".35" stroke-width="4"/>
          <path d="M400 220v185M215 312h370" stroke="{color}" stroke-opacity=".35" stroke-width="6"/>
          <circle cx="400" cy="312" r="48" fill="#080A12" stroke="{color}" stroke-width="8"/>
          <path d="M400 284v56M372 312h56" stroke="#fff" stroke-width="7" stroke-linecap="round"/>
          <text x="400" y="485" text-anchor="middle" font-family="Arial,sans-serif"
                font-size="42" font-weight="900" fill="#fff">VLDST</text>
          <text x="400" y="525" text-anchor="middle" font-family="Arial,sans-serif"
                font-size="24" font-weight="800" fill="{color}">{title}</text>
        """
    elif kind == "premium":
        center = f"""
          <path d="M170 290L240 160L400 270L560 160L630 290L400 440Z"
                fill="{color}" fill-opacity=".9" stroke="#fff" stroke-opacity=".65" stroke-width="5"/>
          <path d="M240 160L400 270L560 160M170 290H630" fill="none"
                stroke="#fff" stroke-opacity=".7" stroke-width="5"/>
          <text x="400" y="505" text-anchor="middle" font-family="Arial,sans-serif"
                font-size="43" font-weight="900" fill="#fff">PREMIUM</text>
        """
    elif kind == "boost":
        center = f"""
          <path d="M455 120L255 340H375L325 500L545 255H420Z"
                fill="{color}" stroke="#fff" stroke-opacity=".7" stroke-width="6"/>
          <circle cx="400" cy="310" r="190" fill="none" stroke="{color}" stroke-opacity=".25" stroke-width="7"/>
          <text x="400" y="570" text-anchor="middle" font-family="Arial,sans-serif"
                font-size="38" font-weight="900" fill="#fff">BOOST</text>
        """
    elif kind == "game":
        center = f"""
          <rect x="160" y="190" width="480" height="250" rx="55"
                fill="#11162A" stroke="{color}" stroke-width="10"/>
          <circle cx="275" cy="315" r="45" fill="{color}" fill-opacity=".3" stroke="{color}" stroke-width="5"/>
          <path d="M250 315h50M275 290v50" stroke="#fff" stroke-width="8" stroke-linecap="round"/>
          <circle cx="490" cy="285" r="12" fill="{color}"/>
          <circle cx="530" cy="325" r="12" fill="#fff"/>
          <text x="400" y="515" text-anchor="middle" font-family="Arial,sans-serif"
                font-size="42" font-weight="900" fill="#fff">VLDST RUSH</text>
        """
    elif kind == "ref":
        center = f"""
          <circle cx="320" cy="265" r="55" fill="{color}"/>
          <circle cx="480" cy="265" r="55" fill="{color}" fill-opacity=".65"/>
          <path d="M205 485C220 390 285 350 320 350C355 350 420 390 435 485
                   M365 485C380 390 445 350 480 350C515 350 580 390 595 485"
                fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="14"
                stroke-linecap="round"/>
          <text x="400" y="560" text-anchor="middle" font-family="Arial,sans-serif"
                font-size="38" font-weight="900" fill="#fff">REFERRALS</text>
        """

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800">
      <defs>
        <radialGradient id="bg" cx="50%" cy="20%" r="80%">
          <stop offset="0%" stop-color="{color}" stop-opacity=".28"/>
          <stop offset="48%" stop-color="#11152A"/>
          <stop offset="100%" stop-color="#05060B"/>
        </radialGradient>
        <filter id="blur"><feGaussianBlur stdDeviation="28"/></filter>
      </defs>
      <rect width="800" height="800" rx="80" fill="url(#bg)"/>
      <circle cx="130" cy="120" r="150" fill="{color}" opacity=".18" filter="url(#blur)"/>
      <circle cx="680" cy="680" r="180" fill="{color}" opacity=".12" filter="url(#blur)"/>
      <rect x="48" y="48" width="704" height="704" rx="60"
            fill="#0B0D17" fill-opacity=".55" stroke="{color}" stroke-opacity=".65" stroke-width="5"/>
      {center}
      <text x="400" y="690" text-anchor="middle" font-family="Arial,sans-serif"
            font-size="22" fill="#A5A8BE">{subtitle}</text>
      <text x="400" y="725" text-anchor="middle" font-family="Arial,sans-serif"
            font-size="18" fill="#777B98">VLDST CASE • MOBILE</text>
    </svg>
    """
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def seed(con):
    cases = [
        ("NEON", "Неоновая коллекция", "#8b5cf6", 1000, 10),
        ("VOID", "Тёмная коллекция", "#38bdf8", 2500, 20),
        ("PHANTOM", "Призрачная коллекция", "#a855f7", 5000, 35),
        ("ROYAL", "Королевская коллекция", "#f59e0b", 10000, 60),
        ("MYTHIC", "Мифическая коллекция", "#ef4444", 25000, 120),
        ("VLDST", "Эксклюзивная коллекция", "#22d3ee", 50000, 200),
    ]

    rarities = [
        ("Common", "common", "#64748b", 45),
        ("Rare", "rare", "#3b82f6", 28),
        ("Epic", "epic", "#a855f7", 15),
        ("Legendary", "legendary", "#f97316", 8),
        ("Mythic", "mythic", "#facc15", 4),
    ]

    with con.cursor() as cur:
        for name, desc, color, coins, stars in cases:
            cur.execute(
                """
                INSERT INTO cases(name,description,image_url,price_coins,price_stars)
                VALUES(%s,%s,%s,%s,%s) RETURNING id
                """,
                (name, desc, svg_data(name, "CASE", color, "case"), coins, stars),
            )
            cid = cur.fetchone()["id"]

            for rar, cls, col, _ in rarities:
                sell = max(50, coins // {"common": 20, "rare": 10, "epic": 4, "legendary": 2, "mythic": 1}[cls])
                item_name = f"{name} {rar}"
                cur.execute(
                    """
                    INSERT INTO items(case_id,name,rarity,image_url,sell_price,weight)
                    VALUES(%s,%s,%s,%s,%s,%s)
                    """,
                    (cid, item_name, cls, svg_data(item_name, rar.upper(), col), sell, 1),
                )


def validate(init_data):
    if not init_data:
        return None
    try:
        p = dict(parse_qsl(init_data, keep_blank_values=True))
        received = p.pop("hash", None)
        if not received:
            return None

        auth_date = int(p.get("auth_date", "0"))
        if auth_date <= 0 or time.time() - auth_date > 86400:
            return None

        check = "\n".join(f"{k}={v}" for k, v in sorted(p.items()))
        secret = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        calculated = hmac.new(
            secret, check.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated, received):
            return None

        user = json.loads(p.get("user", "{}"))
        return user if user.get("id") else None
    except Exception:
        return None


def current_user():
    tg_user = validate(request.headers.get("X-Telegram-Init-Data", ""))
    if not tg_user:
        return None

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE telegram_id=%s FOR UPDATE",
                (tg_user["id"],),
            )
            row = cur.fetchone()

            if not row:
                cur.execute(
                    """
                    INSERT INTO users(telegram_id,username,first_name)
                    VALUES(%s,%s,%s) RETURNING *
                    """,
                    (
                        tg_user["id"],
                        tg_user.get("username"),
                        tg_user.get("first_name") or "Игрок",
                    ),
                )
                row = cur.fetchone()
            else:
                cur.execute(
                    """
                    UPDATE users
                    SET username=%s, first_name=%s
                    WHERE telegram_id=%s
                    RETURNING *
                    """,
                    (
                        tg_user.get("username"),
                        tg_user.get("first_name") or "Игрок",
                        tg_user["id"],
                    ),
                )
                row = cur.fetchone()
        con.commit()

    return row


def require_user():
    user = current_user()
    if not user:
        return None, (jsonify(error="unauthorized"), 401)
    if user["banned"]:
        return None, (jsonify(error="banned"), 403)
    return user, None


def require_admin():
    user, error = require_user()
    if error:
        return None, error
    if user["telegram_id"] not in ADMIN_IDS:
        return None, (jsonify(error="admin_required"), 403)
    return user, None


def uj(user):
    return {
        "telegram_id": user["telegram_id"],
        "username": user["username"],
        "first_name": user["first_name"],
        "coins": user["coins"],
        "stars": user["stars"],
        "xp": user["xp"],
        "level": user["level"],
        "premium_until": user["premium_until"].isoformat() if user["premium_until"] else None,
        "banned": user["banned"],
    }


def refresh_level(cur, user_id):
    cur.execute(
        """
        UPDATE users
        SET level = GREATEST(1, FLOOR(xp / 100.0)::INT + 1)
        WHERE id=%s
        RETURNING *
        """,
        (user_id,),
    )
    return cur.fetchone()


def boost_active(cur, user_id, boost_type):
    cur.execute(
        """
        SELECT 1 FROM boosts
        WHERE user_id=%s AND type=%s AND expires_at>NOW()
        LIMIT 1
        """,
        (user_id, boost_type),
    )
    return cur.fetchone() is not None


def get_case_item_fixed(cur, cid, user_id):
    """
    Fixed rotation instead of random paid loot:
    every opening advances through the case's item list.
    """
    cur.execute(
        """
        SELECT i.*
        FROM items i
        JOIN cases c ON c.id=i.case_id
        WHERE i.case_id=%s
        ORDER BY i.id
        """,
        (cid,),
    )
    items = cur.fetchall()
    if not items:
        return None

    cur.execute(
        """
        SELECT COUNT(*) AS n
        FROM inventory inv
        JOIN items old ON old.id=inv.item_id
        WHERE inv.user_id=%s AND old.case_id=%s
        """,
        (user_id, cid),
    )
    count = int(cur.fetchone()["n"])
    return items[count % len(items)]


@app.get("/health")
def health():
    return jsonify(ok=True, service="VLDST CASE")


@app.get("/")
@app.get("/index.html")
@app.get("/webapp")
@app.get("/webapp/")
def webapp_index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/webapp/<path:filename>")
def webapp_file(filename):
    return send_from_directory(WEB_DIR, filename)


@app.get("/admin")
@app.get("/admin/")
def admin():
    return send_from_directory(WEB_DIR, "admin.html")


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.get("/api/user")
def api_user():
    user, error = require_user()
    return error or jsonify(uj(user))


@app.get("/api/cases")
def api_cases():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM cases WHERE active=TRUE ORDER BY id"
            )
            rows = cur.fetchall()

    return jsonify(cases=[dict(r) for r in rows])


@app.get("/api/cases/<int:cid>/items")
def api_items(cid):
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM items WHERE case_id=%s ORDER BY id",
                (cid,),
            )
            rows = cur.fetchall()

    return jsonify(items=[dict(r) for r in rows])


@app.post("/api/cases/<int:cid>/open")
def open_case(cid):
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM cases WHERE id=%s AND active=TRUE FOR UPDATE",
                (cid,),
            )
            case = cur.fetchone()
            if not case:
                return jsonify(error="case_not_found"), 404

            if user["coins"] < case["price_coins"]:
                return jsonify(error="not_enough_coins"), 400

            item = get_case_item_fixed(cur, cid, user["id"])
            if not item:
                return jsonify(error="case_has_no_items"), 400

            xp_gain = 10 * (2 if boost_active(cur, user["id"], "x2_xp") else 1)
            cur.execute(
                """
                UPDATE users
                SET coins=coins-%s,
                    xp=xp+%s
                WHERE id=%s
                """,
                (case["price_coins"], xp_gain, user["id"]),
            )
            new_user = refresh_level(cur, user["id"])

            cur.execute(
                "INSERT INTO inventory(user_id,item_id) VALUES(%s,%s)",
                (user["id"], item["id"]),
            )
        con.commit()

    return jsonify(item=dict(item), user=uj(new_user), fixed_reward=True)


@app.get("/api/inventory")
def inventory():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT i.id AS inventory_id,it.id,it.name,it.rarity,
                       it.image_url,it.sell_price
                FROM inventory i
                JOIN items it ON it.id=i.item_id
                WHERE i.user_id=%s AND i.sold_at IS NULL
                ORDER BY i.id DESC
                """,
                (user["id"],),
            )
            rows = cur.fetchall()

    return jsonify(inventory=[dict(r) for r in rows])


@app.post("/api/inventory/<int:iid>/sell")
def sell(iid):
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT i.id,it.sell_price
                FROM inventory i
                JOIN items it ON it.id=i.item_id
                WHERE i.id=%s AND i.user_id=%s AND i.sold_at IS NULL
                FOR UPDATE
                """,
                (iid, user["id"]),
            )
            row = cur.fetchone()
            if not row:
                return jsonify(error="item_not_found"), 404

            cur.execute(
                "UPDATE inventory SET sold_at=NOW() WHERE id=%s",
                (iid,),
            )
            multiplier = 2 if boost_active(cur, user["id"], "x2_coins") else 1
            cur.execute(
                """
                UPDATE users SET coins=coins+%s
                WHERE id=%s RETURNING coins
                """,
                (int(row["sell_price"]) * multiplier, user["id"]),
            )
            coins = cur.fetchone()["coins"]
        con.commit()

    return jsonify(
        sold_for=int(row["sell_price"]) * multiplier,
        coins=coins,
        boost_applied=bool(multiplier > 1),
    )


@app.post("/api/daily")
def daily():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT daily_claimed_at FROM users WHERE id=%s FOR UPDATE",
                (user["id"],),
            )
            last = cur.fetchone()["daily_claimed_at"]

            if last and last.astimezone(timezone.utc).date() == now().date():
                return jsonify(error="already_claimed"), 400

            reward = 1000 * (2 if boost_active(cur, user["id"], "x2_coins") else 1)
            cur.execute(
                """
                UPDATE users SET coins=coins+%s,xp=xp+25
                WHERE id=%s
                """,
                (reward, user["id"]),
            )
            new_user = refresh_level(cur, user["id"])
            cur.execute(
                "UPDATE users SET daily_claimed_at=NOW() WHERE id=%s",
                (user["id"],),
            )
        con.commit()

    return jsonify(reward=reward, user=uj(new_user))


@app.get("/api/referrals")
def refs():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM users WHERE referred_by=%s",
                (user["telegram_id"],),
            )
            count = int(cur.fetchone()["n"])

    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user['telegram_id']}"
    return jsonify(
        count=count,
        earned=count * 500,
        referral_link=link,
    )


@app.get("/api/tasks")
def tasks():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT t.*,
                       EXISTS(
                         SELECT 1 FROM task_claims tc
                         WHERE tc.task_id=t.id AND tc.user_id=%s
                       ) AS claimed
                FROM tasks t
                WHERE t.active=TRUE
                ORDER BY t.id
                """,
                (user["id"],),
            )
            rows = cur.fetchall()

    return jsonify(tasks=[dict(r) for r in rows])


@app.post("/api/tasks/<int:tid>/claim")
def claim(tid):
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM tasks WHERE id=%s AND active=TRUE",
                (tid,),
            )
            task = cur.fetchone()
            if not task:
                return jsonify(error="task_not_found"), 404

            cur.execute(
                "SELECT 1 FROM task_claims WHERE user_id=%s AND task_id=%s",
                (user["id"], tid),
            )
            if cur.fetchone():
                return jsonify(error="already_claimed"), 400

            coins = int(task["reward_coins"])
            if boost_active(cur, user["id"], "x2_coins"):
                coins *= 2

            cur.execute(
                "INSERT INTO task_claims(user_id,task_id) VALUES(%s,%s)",
                (user["id"], tid),
            )
            cur.execute(
                """
                UPDATE users
                SET coins=coins+%s,stars=stars+%s,xp=xp+50
                WHERE id=%s
                """,
                (coins, task["reward_stars"], user["id"]),
            )
            new_user = refresh_level(cur, user["id"])
        con.commit()

    return jsonify(ok=True, reward_coins=coins, user=uj(new_user))


@app.post("/api/minigame/play")
def mini():
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    # A short skill game: 0..40 valid taps, reward is capped server-side.
    score = max(0, min(score, 40))
    reward = min(600, 50 + score * 10)
    with db() as con:
        with con.cursor() as cur:
            if boost_active(cur, user["id"], "x2_coins"):
                reward *= 2

            xp_gain = max(5, score // 2)
            if boost_active(cur, user["id"], "x2_xp"):
                xp_gain *= 2

            cur.execute(
                """
                UPDATE users SET coins=coins+%s,xp=xp+%s
                WHERE id=%s
                """,
                (reward, xp_gain, user["id"]),
            )
            new_user = refresh_level(cur, user["id"])
        con.commit()

    return jsonify(score=score, reward=reward, user=uj(new_user))


@app.get("/api/leaderboard")
def leaderboard():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT first_name,username,level,xp
                FROM users
                WHERE banned=FALSE
                ORDER BY xp DESC,level DESC,id ASC
                LIMIT 50
                """
            )
            rows = cur.fetchall()

    return jsonify(leaderboard=[dict(r) for r in rows])


@app.get("/api/boosts")
def boosts():
    user, error = require_user()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM boosts WHERE expires_at<=NOW()")
            cur.execute(
                """
                SELECT type,expires_at
                FROM boosts
                WHERE user_id=%s
                ORDER BY expires_at
                """,
                (user["id"],),
            )
            rows = cur.fetchall()
        con.commit()

    return jsonify(boosts=[dict(r) for r in rows])


@app.get("/api/shop")
def shop():
    user, error = require_user()
    if error:
        return error

    return jsonify(
        balance_products=[
            {"id": "stars_50", "title": "50 внутренних Stars", "stars": 50},
            {"id": "stars_150", "title": "150 внутренних Stars", "stars": 150},
            {"id": "stars_500", "title": "500 внутренних Stars", "stars": 500},
        ],
        store_products=[
            {
                "id": "premium_30",
                "type": "premium",
                "title": "Premium 30 дней",
                "description": "👑 Премиум-статус на 30 дней",
                "stars": 100,
            },
            {
                "id": "boost_x2",
                "type": "boost",
                "title": "x2 Coins",
                "description": "⚡ Удваивает Coins от заданий, daily и продажи",
                "stars": 50,
            },
            {
                "id": "boost_xp",
                "type": "boost",
                "title": "x2 XP",
                "description": "⚡ Удваивает получаемый XP на 24 часа",
                "stars": 50,
            },
        ],
    )


PRODUCT_PRICES = {
    "stars_50": 50,
    "stars_150": 150,
    "stars_500": 500,
    "premium_30": 100,
    "boost_x2": 50,
    "boost_xp": 50,
}


def payment_payload(tid, kind, product):
    import secrets
    return f"vldst:{tid}:{kind}:{product}:{secrets.token_hex(8)}"


async def make_invoice(tid, kind, product, amount):
    payload = payment_payload(tid, kind, product)

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO payments(telegram_id,payload,kind,product_id,amount)
                VALUES(%s,%s,%s,%s,%s)
                """,
                (tid, payload, kind, product, amount),
            )
        con.commit()

    invoice = await bot_instance.create_invoice_link(
        title="VLDST CASE",
        description=f"Покупка: {product}",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=product, amount=amount)],
    )
    return invoice


@app.post("/api/stars/invoice")
def invoice():
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    kind = str(data.get("kind") or "")
    product = str(data.get("product") or data.get("case_id") or "")

    if kind == "case":
        try:
            cid = int(data.get("case_id"))
        except (TypeError, ValueError):
            return jsonify(error="case_not_found"), 400

        with db() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT price_stars FROM cases WHERE id=%s AND active=TRUE",
                    (cid,),
                )
                row = cur.fetchone()

        if not row:
            return jsonify(error="case_not_found"), 404
        amount = int(row["price_stars"])
        product = str(cid)

    else:
        amount = PRODUCT_PRICES.get(product)
        if not amount:
            return jsonify(error="product_not_found"), 400

    if BOT_LOOP is None or bot_instance is None:
        return jsonify(error="payment_unavailable"), 503

    try:
        future = asyncio.run_coroutine_threadsafe(
            make_invoice(user["telegram_id"], kind, product, amount),
            BOT_LOOP,
        )
        return jsonify(invoice_url=future.result(timeout=15))
    except Exception as exc:
        app.logger.exception("Invoice error")
        return jsonify(error="invoice_failed", message=str(exc)), 500


def admin_update(sql, args):
    user, error = require_admin()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(sql, args)
        con.commit()

    return jsonify(ok=True)


@app.get("/api/admin/stats")
def admin_stats():
    user, error = require_admin()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM users")
            users = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM users WHERE banned")
            banned = cur.fetchone()["n"]
            cur.execute("SELECT COALESCE(SUM(coins),0) AS n FROM users")
            coins = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM inventory WHERE sold_at IS NULL")
            inv = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM cases WHERE active")
            cases = cur.fetchone()["n"]

    return jsonify(
        users=users,
        banned=banned,
        coins=coins,
        inventory=inv,
        active_cases=cases,
    )


@app.get("/api/admin/users")
def admin_users():
    user, error = require_admin()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT telegram_id,username,first_name,coins,stars,level,banned
                FROM users ORDER BY id DESC LIMIT 1000
                """
            )
            rows = cur.fetchall()

    return jsonify(users=[dict(r) for r in rows])


@app.get("/api/admin/cases")
def admin_cases():
    user, error = require_admin()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT id,name,price_coins,price_stars,active FROM cases ORDER BY id"
            )
            rows = cur.fetchall()

    return jsonify(cases=[dict(r) for r in rows])


@app.post("/api/admin/give-coins")
def give_coins():
    data = request.get_json(silent=True) or {}
    try:
        tid = int(data["telegram_id"])
        amount = int(data.get("amount", 10000))
    except (KeyError, TypeError, ValueError):
        return jsonify(error="invalid_request"), 400

    if amount <= 0 or amount > 1_000_000_000:
        return jsonify(error="invalid_amount"), 400

    return admin_update(
        "UPDATE users SET coins=coins+%s WHERE telegram_id=%s",
        (amount, tid),
    )


@app.post("/api/admin/give-stars")
def give_stars():
    data = request.get_json(silent=True) or {}
    try:
        tid = int(data["telegram_id"])
        amount = int(data.get("amount", 100))
    except (KeyError, TypeError, ValueError):
        return jsonify(error="invalid_request"), 400

    if amount <= 0 or amount > 1_000_000:
        return jsonify(error="invalid_amount"), 400

    return admin_update(
        "UPDATE users SET stars=stars+%s WHERE telegram_id=%s",
        (amount, tid),
    )


@app.post("/api/admin/user/<int:tid>/premium")
def admin_premium(tid):
    return admin_update(
        """
        UPDATE users
        SET premium_until=GREATEST(COALESCE(premium_until,NOW()),NOW())
                          + INTERVAL '30 days'
        WHERE telegram_id=%s
        """,
        (tid,),
    )


@app.post("/api/admin/user/<int:tid>/ban")
def admin_ban(tid):
    data = request.get_json(silent=True) or {}
    return admin_update(
        "UPDATE users SET banned=%s WHERE telegram_id=%s",
        (bool(data.get("banned")), tid),
    )


@app.post("/api/admin/cases/<int:cid>/toggle")
def admin_toggle_case(cid):
    user, error = require_admin()
    if error:
        return error

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE cases SET active=NOT active WHERE id=%s",
                (cid,),
            )
            if cur.rowcount == 0:
                return jsonify(error="case_not_found"), 404
        con.commit()

    return jsonify(ok=True)


async def send_broadcast(text):
    sent = failed = 0

    with db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT telegram_id FROM users WHERE banned=FALSE")
            ids = [int(r["telegram_id"]) for r in cur.fetchall()]

    for tid in ids:
        try:
            await bot_instance.send_message(
                tid,
                text,
                parse_mode=ParseMode.HTML,
            )
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1

    return sent, failed


@app.post("/api/admin/broadcast")
def admin_broadcast():
    user, error = require_admin()
    if error:
        return error

    text = str((request.get_json(silent=True) or {}).get("text", "")).strip()
    if not text:
        return jsonify(error="empty_text"), 400
    if len(text) > 4096:
        return jsonify(error="text_too_long"), 400

    if BOT_LOOP is None or bot_instance is None:
        return jsonify(error="bot_unavailable"), 503

    try:
        future = asyncio.run_coroutine_threadsafe(
            send_broadcast(text), BOT_LOOP
        )
        sent, failed = future.result(timeout=120)
        return jsonify(sent=sent, failed=failed)
    except Exception as exc:
        app.logger.exception("Broadcast error")
        return jsonify(error="broadcast_failed", message=str(exc)), 500


router = Router()


@router.message(CommandStart())
async def start(message: Message):
    referral = None
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            referral = int(parts[1][4:])
        except ValueError:
            referral = None

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE telegram_id=%s",
                (message.from_user.id,),
            )
            exists = cur.fetchone()

            if not exists:
                ref = referral if referral != message.from_user.id else None
                cur.execute(
                    """
                    INSERT INTO users(telegram_id,username,first_name,referred_by)
                    VALUES(%s,%s,%s,%s)
                    """,
                    (
                        message.from_user.id,
                        message.from_user.username,
                        message.from_user.first_name or "Игрок",
                        ref,
                    ),
                )

                if ref:
                    cur.execute(
                        "UPDATE users SET coins=coins+500 WHERE telegram_id=%s",
                        (ref,),
                    )
        con.commit()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Открыть VLDST CASE",
                    web_app=WebAppInfo(url=WEBAPP_URL + "/webapp/"),
                )
            ]
        ]
    )

    await message.answer(
        "🔥 <b>VLDST CASE</b>\n\n"
        "Кейсы • Coins • Stars • Premium • рейтинг\n"
        "Награды в кейсах выдаются по фиксированной последовательности.",
        reply_markup=keyboard,
    )


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещён.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ Открыть ADMIN",
                    web_app=WebAppInfo(url=WEBAPP_URL + "/admin/"),
                )
            ]
        ]
    )
    await message.answer("🛠 <b>VLDST ADMIN</b>", reply_markup=keyboard)


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def paid(message: Message):
    payment = message.successful_payment

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT * FROM payments WHERE payload=%s FOR UPDATE",
                (payment.invoice_payload,),
            )
            row = cur.fetchone()

            if not row or row["status"] == "paid":
                return

            # Confirm the currency and amount recorded before applying anything.
            if payment.currency != "XTR" or int(payment.total_amount) != int(row["amount"]):
                return

            cur.execute(
                "UPDATE payments SET status='paid' WHERE payload=%s",
                (payment.invoice_payload,),
            )

            tid = int(row["telegram_id"])

            if row["kind"] == "balance":
                cur.execute(
                    "UPDATE users SET stars=stars+%s WHERE telegram_id=%s",
                    (row["amount"], tid),
                )

            elif row["product_id"] == "premium_30":
                cur.execute(
                    """
                    UPDATE users
                    SET premium_until=GREATEST(COALESCE(premium_until,NOW()),NOW())
                                      + INTERVAL '30 days'
                    WHERE telegram_id=%s
                    """,
                    (tid,),
                )

            elif row["product_id"] == "boost_x2":
                cur.execute(
                    """
                    INSERT INTO boosts(user_id,type,expires_at)
                    SELECT id,'x2_coins',NOW()+INTERVAL '24 hours'
                    FROM users WHERE telegram_id=%s
                    """,
                    (tid,),
                )

            elif row["product_id"] == "boost_xp":
                cur.execute(
                    """
                    INSERT INTO boosts(user_id,type,expires_at)
                    SELECT id,'x2_xp',NOW()+INTERVAL '24 hours'
                    FROM users WHERE telegram_id=%s
                    """,
                    (tid,),
                )

            elif row["kind"] == "case":
                try:
                    cid = int(row["product_id"])
                except ValueError:
                    cid = 0

                cur.execute(
                    "SELECT id FROM users WHERE telegram_id=%s",
                    (tid,),
                )
                user_row = cur.fetchone()

                if user_row:
                    chosen = get_case_item_fixed(cur, cid, user_row["id"])
                    if chosen:
                        cur.execute(
                            """
                            INSERT INTO inventory(user_id,item_id)
                            VALUES(%s,%s)
                            """,
                            (user_row["id"], chosen["id"]),
                        )
                        cur.execute(
                            "UPDATE users SET xp=xp+10 WHERE id=%s",
                            (user_row["id"],),
                        )
                        refresh_level(cur, user_row["id"])

        con.commit()

    await message.answer(
        "⭐ Оплата подтверждена!\n"
        "Награда добавлена в инвентарь."
    )


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify(error="not_found"), 404
    return "VLDST CASE: страница не найдена", 404


@app.errorhandler(500)
def server_error(error):
    app.logger.exception("Unhandled server error")
    if request.path.startswith("/api/"):
        return jsonify(error="server_error"), 500
    return "VLDST CASE: ошибка сервера", 500


async def main():
    global BOT_LOOP, bot_instance

    BOT_LOOP = asyncio.get_running_loop()
    init_db()

    bot_instance = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    port = int(os.getenv("PORT", "10000"))

    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    ).start()

    await bot_instance.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot_instance)


if __name__ == "__main__":
    asyncio.run(main())
