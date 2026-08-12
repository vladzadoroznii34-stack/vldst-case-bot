import os, asyncio, hashlib, hmac, json, random
from urllib.parse import parse_qsl
from threading import Thread
import psycopg
from flask import Flask, send_from_directory, request
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message
from dotenv import load_dotenv

load_dotenv()
TOKEN=os.getenv("BOT_TOKEN")
DATABASE_URL=os.getenv("DATABASE_URL")
ADMIN_ID=int(os.getenv("ADMIN_ID","6038067496"))
WEBAPP_URL="https://vldst-case-bot.onrender.com/webapp/index.html"
ADMIN_URL="https://vldst-case-bot.onrender.com/webapp/admin.html"
BOT_USERNAME="VLDSTCaseBot"

if not TOKEN: raise RuntimeError("BOT_TOKEN не найден")
if not DATABASE_URL: raise RuntimeError("DATABASE_URL не найден")

app=Flask(__name__)

@app.route("/")
def home(): return "VLDST Backend is running!"

@app.route("/health")
def health(): return {"status":"ok","project":"VLDST CASE"}

@app.route("/webapp/<path:filename>")
def webapp(filename): return send_from_directory("webapp",filename)

def verify_telegram_init_data(init_data):
    if not init_data: return None
    try:
        data=dict(parse_qsl(init_data,keep_blank_values=True))
        received_hash=data.pop("hash",None)
        if not received_hash: return None
        check="\n".join(f"{k}={v}" for k,v in sorted(data.items()))
        secret=hmac.new(b"WebAppData",TOKEN.encode(),hashlib.sha256).digest()
        calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc,received_hash): return None
        raw=data.get("user")
        return json.loads(raw) if raw else None
    except Exception: return None

def get_telegram_user():
    return verify_telegram_init_data(request.headers.get("X-Telegram-Init-Data",""))

def is_admin():
    u=get_telegram_user()
    try: return bool(u) and int(u.get("id",0))==ADMIN_ID
    except Exception: return False

def init_database():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS users(
                id BIGSERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT, first_name TEXT, coins BIGINT NOT NULL DEFAULT 0,
                stars BIGINT NOT NULL DEFAULT 0, level INTEGER NOT NULL DEFAULT 1,
                xp BIGINT NOT NULL DEFAULT 0, referral_code TEXT UNIQUE,
                referred_by BIGINT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());""")
            c.execute("""CREATE TABLE IF NOT EXISTS cases(
                id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,description TEXT,
                price_coins BIGINT NOT NULL DEFAULT 0,price_stars INTEGER NOT NULL DEFAULT 0,
                image_url TEXT,active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());""")
            c.execute("""CREATE TABLE IF NOT EXISTS items(
                id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,description TEXT,
                rarity TEXT NOT NULL,sell_price BIGINT NOT NULL DEFAULT 0,image_url TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());""")
            c.execute("""CREATE TABLE IF NOT EXISTS case_items(
                id BIGSERIAL PRIMARY KEY,case_id BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                drop_chance NUMERIC(8,5) NOT NULL);""")
            c.execute("""CREATE TABLE IF NOT EXISTS inventory(
                id BIGSERIAL PRIMARY KEY,telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                item_id BIGINT NOT NULL REFERENCES items(id),obtained_from TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());""")
            c.execute("""CREATE TABLE IF NOT EXISTS transactions(
                id BIGSERIAL PRIMARY KEY,telegram_id BIGINT,type TEXT NOT NULL,
                amount BIGINT NOT NULL DEFAULT 0,description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());""")
        conn.commit()

def create_or_update_user(tid,username,first_name,ref=None):
    code=f"VLDST{tid}"
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""INSERT INTO users(telegram_id,username,first_name,referral_code,referred_by)
                VALUES(%s,%s,%s,%s,NULL) ON CONFLICT(telegram_id)
                DO UPDATE SET username=EXCLUDED.username,first_name=EXCLUDED.first_name
                RETURNING coins,stars,level,xp,referred_by""",(tid,username,first_name,code))
            row=c.fetchone()
            # Referral is applied only once.
            if ref and ref!=tid and row[4] is None:
                c.execute("SELECT telegram_id FROM users WHERE telegram_id=%s",(ref,))
                if c.fetchone():
                    c.execute("UPDATE users SET referred_by=%s,coins=coins+500 WHERE telegram_id=%s AND referred_by IS NULL",(ref,tid))
                    if c.rowcount:
                        c.execute("UPDATE users SET coins=coins+500 WHERE telegram_id=%s",(ref,))
                        c.execute("""INSERT INTO transactions(telegram_id,type,amount,description)
                            VALUES(%s,'REFERRAL_REWARD',500,'Бонус приглашённому игроку'),
                                  (%s,'REFERRAL_REWARD',500,'Награда за приглашённого игрока')""",(tid,ref))
            conn.commit()
    return row

@app.route("/api/user")
def api_user():
    u=get_telegram_user()
    if not u:return {"error":"unauthorized"},401
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""SELECT telegram_id,username,first_name,coins,stars,level,xp,referral_code,referred_by
                         FROM users WHERE telegram_id=%s""",(int(u["id"]),))
            r=c.fetchone()
    if not r:return {"error":"user_not_found"},404
    return dict(telegram_id=r[0],username=r[1],first_name=r[2],coins=r[3],stars=r[4],
                level=r[5],xp=r[6],referral_code=r[7],referred_by=r[8])

@app.route("/api/referrals")
def api_referrals():
    u=get_telegram_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM users WHERE referred_by=%s",(tid,))
            count=c.fetchone()[0]
            c.execute("""SELECT COALESCE(SUM(amount),0) FROM transactions
                         WHERE telegram_id=%s AND type='REFERRAL_REWARD'""",(tid,))
            earned=int(c.fetchone()[0] or 0)
    return {"referral_link":f"https://t.me/{BOT_USERNAME}?start=ref_{tid}","count":count,"earned":earned}

@app.route("/api/cases")
def api_cases():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("SELECT id,name,description,price_coins,price_stars,image_url FROM cases WHERE active=TRUE ORDER BY id")
            rows=c.fetchall()
    return {"cases":[{"id":r[0],"name":r[1],"description":r[2],"price_coins":r[3],"price_stars":r[4],"image_url":r[5]} for r in rows]}

@app.route("/api/cases/<int:case_id>/items")
def public_case_items(case_id):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""SELECT items.id,items.name,items.description,items.rarity,items.sell_price,
                         items.image_url,case_items.drop_chance FROM case_items
                         JOIN items ON items.id=case_items.item_id WHERE case_items.case_id=%s
                         ORDER BY case_items.drop_chance DESC""",(case_id,))
            rows=c.fetchall()
    return {"items":[{"id":r[0],"name":r[1],"description":r[2],"rarity":r[3],"sell_price":r[4],
                      "image_url":r[5],"drop_chance":float(r[6])} for r in rows]}

@app.route("/api/inventory")
def api_inventory():
    u=get_telegram_user()
    if not u:return {"error":"unauthorized"},401
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""SELECT inventory.id,items.id,items.name,items.description,items.rarity,
                         items.sell_price,items.image_url,inventory.obtained_from,inventory.created_at
                         FROM inventory JOIN items ON items.id=inventory.item_id
                         WHERE inventory.telegram_id=%s ORDER BY inventory.created_at DESC""",(int(u["id"]),))
            rows=c.fetchall()
    return {"inventory":[{"inventory_id":r[0],"item_id":r[1],"name":r[2],"description":r[3],"rarity":r[4],
                         "sell_price":r[5],"image_url":r[6],"obtained_from":r[7],"created_at":r[8].isoformat()} for r in rows]}

@app.route("/api/inventory/<int:inventory_id>/sell",methods=["POST"])
def sell_item(inventory_id):
    u=get_telegram_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""SELECT inventory.id,items.name,items.sell_price FROM inventory
                         JOIN items ON items.id=inventory.item_id
                         WHERE inventory.id=%s AND inventory.telegram_id=%s FOR UPDATE""",(inventory_id,tid))
            r=c.fetchone()
            if not r:return {"error":"inventory_item_not_found"},404
            price=int(r[2] or 0)
            if price<=0:return {"error":"item_cannot_be_sold"},400
            c.execute("DELETE FROM inventory WHERE id=%s AND telegram_id=%s",(inventory_id,tid))
            c.execute("UPDATE users SET coins=coins+%s WHERE telegram_id=%s RETURNING coins",(price,tid))
            coins=int(c.fetchone()[0])
            c.execute("""INSERT INTO transactions(telegram_id,type,amount,description)
                         VALUES(%s,'ITEM_SELL',%s,%s)""",(tid,price,f"Продажа предмета: {r[1]}"))
        conn.commit()
    return {"success":True,"coins":coins,"sold_for":price}

@app.route("/api/cases/<int:case_id>/open",methods=["POST"])
def open_case(case_id):
    u=get_telegram_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("SELECT coins FROM users WHERE telegram_id=%s FOR UPDATE",(tid,))
            ur=c.fetchone()
            if not ur:return {"error":"user_not_found"},404
            c.execute("SELECT id,name,price_coins,price_stars FROM cases WHERE id=%s AND active=TRUE",(case_id,))
            case=c.fetchone()
            if not case:return {"error":"case_not_found"},404
            price=int(case[2] or 0); coins=int(ur[0])
            if coins<price:return {"error":"not_enough_coins"},400
            c.execute("""SELECT items.id,items.name,items.description,items.rarity,items.sell_price,
                         items.image_url,case_items.drop_chance FROM case_items
                         JOIN items ON items.id=case_items.item_id WHERE case_items.case_id=%s""",(case_id,))
            items=c.fetchall()
            if not items:return {"error":"case_has_no_items"},400
            total=sum(float(x[6]) for x in items)
            if total<=0:return {"error":"invalid_drop_chances"},400
            roll=random.uniform(0,total); cur=0; selected=items[-1]
            for x in items:
                cur+=float(x[6])
                if roll<=cur:selected=x;break
            new_coins=coins-price
            c.execute("UPDATE users SET coins=%s WHERE telegram_id=%s",(new_coins,tid))
            c.execute("INSERT INTO inventory(telegram_id,item_id,obtained_from) VALUES(%s,%s,%s)",(tid,selected[0],f"case:{case_id}"))
            c.execute("""INSERT INTO transactions(telegram_id,type,amount,description)
                         VALUES(%s,'CASE_OPEN',%s,%s)""",(tid,-price,f"Открытие кейса #{case_id}"))
        conn.commit()
    return {"success":True,"coins":new_coins,"item":{"id":selected[0],"name":selected[1],
            "description":selected[2],"rarity":selected[3],"sell_price":selected[4],"image_url":selected[5]}}

@app.route("/api/admin/check")
def admin_check():
    if not is_admin():return {"admin":False},403
    return {"admin":True}

@app.route("/api/admin/stats")
def admin_stats():
    if not is_admin():return {"error":"forbidden"},403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            vals=[]
            for table in ("users","cases","items","inventory"):
                c.execute(f"SELECT COUNT(*) FROM {table}"); vals.append(c.fetchone()[0])
    return dict(zip(("users","cases","items","inventory"),vals))

@app.route("/api/admin/give-coins",methods=["POST"])
def admin_give_coins():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {}
    try:tid=int(d.get("telegram_id")); amount=int(d.get("amount"))
    except (TypeError,ValueError):return {"error":"invalid_data"},400
    if amount<=0:return {"error":"amount_must_be_positive"},400
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE users SET coins=coins+%s WHERE telegram_id=%s RETURNING coins",(amount,tid))
            r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            coins=int(r[0])
            c.execute("""INSERT INTO transactions(telegram_id,type,amount,description)
                         VALUES(%s,'ADMIN_GIVE_COINS',%s,'Выдано администратором')""",(tid,amount))
        conn.commit()
    return {"success":True,"telegram_id":tid,"coins":coins,"added":amount}

@app.route("/api/admin/cases",methods=["GET","POST"])
def admin_cases():
    if not is_admin():return {"error":"forbidden"},403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            if request.method=="POST":
                d=request.get_json(silent=True) or {}
                name=str(d.get("name","")).strip()
                if not name:return {"error":"name_required"},400
                try:pc=int(d.get("price_coins",0)); ps=int(d.get("price_stars",0))
                except (TypeError,ValueError):return {"error":"invalid_price"},400
                c.execute("""INSERT INTO cases(name,description,price_coins,price_stars,image_url)
                             VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                          (name,str(d.get("description","")),pc,ps,str(d.get("image_url",""))))
                cid=c.fetchone()[0]; conn.commit(); return {"success":True,"case_id":cid}
            c.execute("SELECT id,name,description,price_coins,price_stars,image_url,active FROM cases ORDER BY id DESC")
            rows=c.fetchall()
    return {"cases":[{"id":r[0],"name":r[1],"description":r[2],"price_coins":r[3],"price_stars":r[4],"image_url":r[5],"active":r[6]} for r in rows]}

@app.route("/api/admin/cases/<int:case_id>/disable",methods=["POST"])
def disable_case(case_id):
    if not is_admin():return {"error":"forbidden"},403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:c.execute("UPDATE cases SET active=FALSE WHERE id=%s",(case_id,))
        conn.commit()
    return {"success":True}

@app.route("/api/admin/items",methods=["GET","POST"])
def admin_items():
    if not is_admin():return {"error":"forbidden"},403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            if request.method=="POST":
                d=request.get_json(silent=True) or {}; name=str(d.get("name","")).strip()
                rarity=str(d.get("rarity","COMMON")).upper().strip()
                try:sell=int(d.get("sell_price",0))
                except (TypeError,ValueError):return {"error":"invalid_sell_price"},400
                if not name:return {"error":"name_required"},400
                if rarity not in {"COMMON","RARE","EPIC","LEGENDARY","MYTHIC"}:return {"error":"invalid_rarity"},400
                c.execute("""INSERT INTO items(name,description,rarity,sell_price,image_url)
                             VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                          (name,str(d.get("description","")),rarity,sell,str(d.get("image_url",""))))
                iid=c.fetchone()[0];conn.commit();return {"success":True,"item_id":iid}
            c.execute("SELECT id,name,description,rarity,sell_price,image_url FROM items ORDER BY id DESC")
            rows=c.fetchall()
    return {"items":[{"id":r[0],"name":r[1],"description":r[2],"rarity":r[3],"sell_price":r[4],"image_url":r[5]} for r in rows]}

@app.route("/api/admin/case-items",methods=["POST"])
def add_case_item():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {}
    try:cid=int(d.get("case_id"));iid=int(d.get("item_id"));chance=float(d.get("drop_chance"))
    except (TypeError,ValueError):return {"error":"invalid_data"},400
    if chance<=0 or chance>100:return {"error":"invalid_chance"},400
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("SELECT id FROM cases WHERE id=%s",(cid,))
            if not c.fetchone():return {"error":"case_not_found"},404
            c.execute("SELECT id FROM items WHERE id=%s",(iid,))
            if not c.fetchone():return {"error":"item_not_found"},404
            c.execute("SELECT COALESCE(SUM(drop_chance),0) FROM case_items WHERE case_id=%s",(cid,))
            if float(c.fetchone()[0])+chance>100:return {"error":"total_chance_exceeds_100"},400
            c.execute("INSERT INTO case_items(case_id,item_id,drop_chance) VALUES(%s,%s,%s)",(cid,iid,chance))
        conn.commit()
    return {"success":True}

@app.route("/api/admin/cases/<int:case_id>/items")
def admin_case_items(case_id):
    if not is_admin():return {"error":"forbidden"},403
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as c:
            c.execute("""SELECT case_items.id,items.id,items.name,items.rarity,case_items.drop_chance
                         FROM case_items JOIN items ON items.id=case_items.item_id
                         WHERE case_items.case_id=%s ORDER BY case_items.drop_chance DESC""",(case_id,))
            rows=c.fetchall()
    items=[{"case_item_id":r[0],"item_id":r[1],"name":r[2],"rarity":r[3],"drop_chance":float(r[4])} for r in rows]
    total=sum(x["drop_chance"] for x in items)
    return {"items":items,"total_chance":total,"remaining_chance":max(0,100-total)}

bot=Bot(token=TOKEN); dp=Dispatcher()

@dp.message(Command("admin"))
async def admin_command(message:Message):
    if message.from_user.id!=ADMIN_ID:
        await message.answer("⛔ Доступ запрещён."); return
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚙️ Открыть админ-панель",web_app=WebAppInfo(url=ADMIN_URL))]])
    await message.answer("🛠 <b>VLDST ADMIN</b>\n\nПанель управления.",reply_markup=kb,parse_mode="HTML")

@dp.message(CommandStart())
async def start(message:Message):
    user=message.from_user; ref=None
    parts=message.text.split(maxsplit=1)
    if len(parts)>1 and parts[1].startswith("ref_"):
        try:ref=int(parts[1][4:])
        except ValueError:pass
    coins,stars,level,xp,_=create_or_update_user(user.id,user.username,user.first_name,ref)
    buttons=[[InlineKeyboardButton(text="🎁 Открыть VLDST",web_app=WebAppInfo(url=WEBAPP_URL))]]
    if user.id==ADMIN_ID:buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель",web_app=WebAppInfo(url=ADMIN_URL))])
    await message.answer(f"🌌 <b>VLDST CASE</b>\n\nДобро пожаловать, <b>{user.first_name}</b>!\n\n🪙 Coins: <b>{coins:,}</b>\n⭐ Stars: <b>{stars}</b>\n🏆 Уровень: <b>{level}</b>\n⚡ XP: <b>{xp}</b>",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),parse_mode="HTML")

def run_web():
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")),threaded=True)

async def main():
    print("Initializing database..."); init_database(); print("Database initialized.")
    print("Starting Telegram bot..."); await dp.start_polling(bot)

if __name__=="__main__":
    Thread(target=run_web,daemon=True).start()
    asyncio.run(main())
