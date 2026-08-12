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
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WEBAPP_URL = "https://vldst-case-bot.onrender.com/webapp/index.html"
ADMIN_URL = "https://vldst-case-bot.onrender.com/webapp/admin.html"

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден")

app = Flask(__name__)

@app.route("/")
def home():
    return "VLDST Backend is running!"

@app.route("/webapp/<path:filename>")
def webapp(filename):
    return send_from_directory("webapp", filename)

def verify_telegram_init_data(init_data):
    if not init_data:
        return None
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = data.pop("hash", None)
        if not received_hash:
            return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return None
        user_data = data.get("user")
        return json.loads(user_data) if user_data else None
    except Exception:
        return None

def get_telegram_user():
    return verify_telegram_init_data(
        request.headers.get("X-Telegram-Init-Data")
    )

def is_admin():
    user = get_telegram_user()
    try:
        return bool(user) and int(user.get("id", 0)) == ADMIN_ID
    except Exception:
        return False

def init_database():
    with psycopg.connect(DATABASE_URL) as conn:
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
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
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
                )
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
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS case_items (
                    id BIGSERIAL PRIMARY KEY,
                    case_id BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                    drop_chance NUMERIC(8,5) NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                    item_id BIGINT NOT NULL REFERENCES items(id),
                    obtained_from TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    type TEXT NOT NULL,
                    amount BIGINT NOT NULL DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()

def create_or_update_user(telegram_id, username, first_name):
    code = f"VLDST{telegram_id}"
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (telegram_id, username, first_name, referral_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
                RETURNING coins, stars, level, xp
            """, (telegram_id, username, first_name, code))
            result = cur.fetchone()
        conn.commit()
    return result

@app.route("/api/user")
def api_user():
    user = get_telegram_user()
    if not user:
        return {"error": "unauthorized"}, 401
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT telegram_id, username, first_name, coins, stars, level, xp, referral_code
                FROM users WHERE telegram_id = %s
            """, (user["id"],))
            row = cur.fetchone()
    if not row:
        return {"error": "user_not_found"}, 404
    return {
        "telegram_id": row[0], "username": row[1], "first_name": row[2],
        "coins": row[3], "stars": row[4], "level": row[5], "xp": row[6],
        "referral_code": row[7]
    }

@app.route("/api/cases")
def api_cases():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, price_coins, price_stars, image_url
                FROM cases WHERE active = TRUE ORDER BY id ASC
            """)
            rows = cur.fetchall()
    return {"cases": [
        {"id": r[0], "name": r[1], "description": r[2],
         "price_coins": r[3], "price_stars": r[4], "image_url": r[5]}
        for r in rows
    ]}

@app.route("/api/inventory")
def api_inventory():
    user = get_telegram_user()
    if not user:
        return {"error": "unauthorized"}, 401
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT inventory.id, items.id, items.name, items.description,
                       items.rarity, items.sell_price, items.image_url,
                       inventory.obtained_from, inventory.created_at
                FROM inventory JOIN items ON items.id = inventory.item_id
                WHERE inventory.telegram_id = %s
                ORDER BY inventory.created_at DESC
            """, (user["id"],))
            rows = cur.fetchall()
    return {"inventory": [
        {"inventory_id": r[0], "item_id": r[1], "name": r[2],
         "description": r[3], "rarity": r[4], "sell_price": r[5],
         "image_url": r[6], "obtained_from": r[7],
         "created_at": r[8].isoformat()}
        for r in rows
    ]}

@app.route("/api/cases/<int:case_id>/open", methods=["POST"])
def open_case(case_id):
    user = get_telegram_user()
    if not user:
        return {"error": "unauthorized"}, 401
    uid = int(user["id"])

    with psycopg.connect(DATABASE_URL) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT coins FROM users WHERE telegram_id=%s FOR UPDATE", (uid,))
                u = cur.fetchone()
                if not u:
                    conn.rollback()
                    return {"error": "user_not_found"}, 404

                cur.execute("""
                    SELECT id, name, price_coins FROM cases
                    WHERE id=%s AND active=TRUE
                """, (case_id,))
                case = cur.fetchone()
                if not case:
                    conn.rollback()
                    return {"error": "case_not_found"}, 404

                price = int(case[2])
                if price <= 0:
                    conn.rollback()
                    return {"error": "invalid_case_price"}, 400
                if int(u[0]) < price:
                    conn.rollback()
                    return {"error": "not_enough_coins", "coins": int(u[0]), "required": price}, 400

                cur.execute("""
                    SELECT items.id, items.name, items.description, items.rarity,
                           items.sell_price, items.image_url, case_items.drop_chance
                    FROM case_items JOIN items ON items.id=case_items.item_id
                    WHERE case_items.case_id=%s
                """, (case_id,))
                drops = cur.fetchall()
                total = sum(float(x[6]) for x in drops)
                if not drops or total <= 0 or total > 100.00001:
                    conn.rollback()
                    return {"error": "invalid_drop_chances"}, 400

                roll = random.uniform(0, total)
                current = 0
                selected = drops[-1]
                for x in drops:
                    current += float(x[6])
                    if roll <= current:
                        selected = x
                        break

                cur.execute("""
                    UPDATE users SET coins=coins-%s, xp=xp+10
                    WHERE telegram_id=%s AND coins >= %s
                """, (price, uid, price))
                if cur.rowcount != 1:
                    conn.rollback()
                    return {"error": "not_enough_coins"}, 400

                cur.execute("""
                    INSERT INTO inventory (telegram_id,item_id,obtained_from)
                    VALUES (%s,%s,%s) RETURNING id
                """, (uid, selected[0], f"case:{case_id}"))
                inventory_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO transactions (telegram_id,type,amount,description)
                    VALUES (%s,%s,%s,%s)
                """, (uid, "CASE_OPEN", -price, f"{case[1]} -> {selected[1]}"))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return {
        "success": True,
        "item": {
            "inventory_id": inventory_id, "id": selected[0], "name": selected[1],
            "description": selected[2], "rarity": selected[3],
            "sell_price": selected[4], "image_url": selected[5],
            "drop_chance": float(selected[6])
        },
        "coins": int(u[0]) - price,
        "xp_added": 10
    }

@app.route("/api/inventory/<int:inventory_id>/sell", methods=["POST"])
def sell_item(inventory_id):
    user = get_telegram_user()
    if not user:
        return {"error": "unauthorized"}, 401
    uid = int(user["id"])

    with psycopg.connect(DATABASE_URL) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT items.name, items.sell_price
                    FROM inventory JOIN items ON items.id=inventory.item_id
                    WHERE inventory.id=%s AND inventory.telegram_id=%s
                    FOR UPDATE
                """, (inventory_id, uid))
                item = cur.fetchone()
                if not item:
                    conn.rollback()
                    return {"error": "inventory_item_not_found"}, 404

                value = int(item[1])
                if value <= 0:
                    conn.rollback()
                    return {"error": "item_cannot_be_sold"}, 400

                cur.execute("DELETE FROM inventory WHERE id=%s AND telegram_id=%s", (inventory_id, uid))
                cur.execute("""
                    UPDATE users SET coins=coins+%s WHERE telegram_id=%s RETURNING coins
                """, (value, uid))
                new_coins = int(cur.fetchone()[0])

                cur.execute("""
                    INSERT INTO transactions (telegram_id,type,amount,description)
                    VALUES (%s,%s,%s,%s)
                """, (uid, "ITEM_SELL", value, f"Sold {item[0]}"))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return {"success": True, "coins_received": value, "coins": new_coins}

@app.route("/api/admin/check")
def admin_check():
    if not is_admin():
        return {"admin": False}, 403
    return {"admin": True}

@app.route("/api/admin/stats")
def admin_stats():
    if not is_admin():
        return {"error": "forbidden"}, 403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users"); users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM cases"); cases = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM items"); items = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM inventory"); inventory = cur.fetchone()[0]
    return {"users": users, "cases": cases, "items": items, "inventory": inventory}

@app.route("/api/admin/cases")
def admin_cases():
    if not is_admin():
        return {"error": "forbidden"}, 403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id,name,description,price_coins,price_stars,image_url,active
                FROM cases ORDER BY id DESC
            """)
            rows = cur.fetchall()
    return {"cases": [
        {"id":r[0],"name":r[1],"description":r[2],"price_coins":r[3],
         "price_stars":r[4],"image_url":r[5],"active":r[6]} for r in rows
    ]}

@app.route("/api/admin/cases", methods=["POST"])
def create_case():
    if not is_admin():
        return {"error": "forbidden"}, 403
    d = request.get_json(silent=True) or {}
    name = str(d.get("name","")).strip()
    if not name:
        return {"error":"name_required"},400
    try:
        coins = int(d.get("price_coins",0))
        stars = int(d.get("price_stars",0))
    except (TypeError,ValueError):
        return {"error":"invalid_price"},400
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cases(name,description,price_coins,price_stars,image_url)
                VALUES(%s,%s,%s,%s,%s) RETURNING id
            """,(name,str(d.get("description","")),coins,stars,str(d.get("image_url",""))))
            cid=cur.fetchone()[0]
        conn.commit()
    return {"success":True,"case_id":cid}

@app.route("/api/admin/items")
def admin_items():
    if not is_admin():
        return {"error":"forbidden"},403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id,name,description,rarity,sell_price,image_url FROM items ORDER BY id DESC")
            rows=cur.fetchall()
    return {"items":[
        {"id":r[0],"name":r[1],"description":r[2],"rarity":r[3],"sell_price":r[4],"image_url":r[5]}
        for r in rows
    ]}

@app.route("/api/admin/items", methods=["POST"])
def create_item():
    if not is_admin():
        return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {}
    name=str(d.get("name","")).strip()
    rarity=str(d.get("rarity","COMMON")).upper().strip()
    if not name:
        return {"error":"name_required"},400
    if rarity not in {"COMMON","RARE","EPIC","LEGENDARY","MYTHIC"}:
        return {"error":"invalid_rarity"},400
    try:
        sell=int(d.get("sell_price",0))
    except (TypeError,ValueError):
        return {"error":"invalid_sell_price"},400
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO items(name,description,rarity,sell_price,image_url)
                VALUES(%s,%s,%s,%s,%s) RETURNING id
            """,(name,str(d.get("description","")),rarity,sell,str(d.get("image_url",""))))
            iid=cur.fetchone()[0]
        conn.commit()
    return {"success":True,"item_id":iid}

@app.route("/api/admin/case-items", methods=["POST"])
def add_case_item():
    if not is_admin():
        return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {}
    try:
        cid=int(d.get("case_id")); iid=int(d.get("item_id")); chance=float(d.get("drop_chance"))
    except (TypeError,ValueError):
        return {"error":"invalid_data"},400
    if chance <= 0 or chance > 100:
        return {"error":"invalid_chance"},400
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(SUM(drop_chance),0) FROM case_items WHERE case_id=%s",(cid,))
            total=float(cur.fetchone()[0])
            if total+chance>100:
                return {"error":"total_chance_exceeds_100"},400
            cur.execute("INSERT INTO case_items(case_id,item_id,drop_chance) VALUES(%s,%s,%s)",(cid,iid,chance))
        conn.commit()
    return {"success":True}

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return
    kb=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚙️ Открыть админ-панель", web_app=WebAppInfo(url=ADMIN_URL))
    ]])
    await message.answer("🛠 <b>VLDST ADMIN</b>\n\nПанель управления проектом.",
                         reply_markup=kb, parse_mode="HTML")

@dp.message(CommandStart())
async def start(message: Message):
    u=message.from_user
    coins,stars,level,xp=create_or_update_user(u.id,u.username,u.first_name)
    buttons=[[
        InlineKeyboardButton(text="🎁 Открыть VLDST", web_app=WebAppInfo(url=WEBAPP_URL))
    ]]
    if u.id==ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель", web_app=WebAppInfo(url=ADMIN_URL))])
    await message.answer(
        f"🌌 <b>VLDST</b>\n\nДобро пожаловать, <b>{u.first_name}</b>!\n\n"
        f"🪙 Coins: <b>{coins:,}</b>\n⭐ Stars: <b>{stars}</b>\n"
        f"⭐ Уровень: <b>{level}</b>\n⚡ XP: <b>{xp}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","10000")))

async def main():
    init_database()
    await dp.start_polling(bot)

if __name__=="__main__":
    Thread(target=run_web,daemon=True).start()
    asyncio.run(main())
