import os, asyncio, hashlib, hmac, json, random, html, urllib.request, urllib.parse, time
from urllib.parse import parse_qsl
from threading import Thread
from datetime import datetime, timezone, timedelta

import psycopg
from flask import Flask, send_from_directory, request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message, PreCheckoutQuery
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6038067496"))
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://vldst-case-bot.onrender.com").rstrip("/")
WEBAPP_URL = os.getenv("WEBAPP_URL", f"{PUBLIC_URL}/webapp/index.html")
ADMIN_URL = os.getenv("ADMIN_URL", f"{PUBLIC_URL}/webapp/admin.html")
BOT_USERNAME = os.getenv("BOT_USERNAME", "VLDSTCaseBot")
if not TOKEN: raise RuntimeError("BOT_TOKEN не найден")
if not DATABASE_URL: raise RuntimeError("DATABASE_URL не найден")

app = Flask(__name__)

CASES = {
    2: ("VLDST CORE", 1000, 15, "core"),
    3: ("VLDST PULSE", 5000, 25, "pulse"),
    4: ("VLDST AURA", 15000, 50, "aura"),
    5: ("VLDST VOID", 30000, 75, "void"),
    6: ("VLDST OVERDRIVE", 60000, 100, "overdrive"),
    7: ("VLDST RIFT", 150000, 110, "rift"),
}
CASE_ITEMS = {2:list(range(6,14)),3:list(range(14,22)),4:list(range(22,31)),5:list(range(31,39)),6:list(range(39,47)),7:list(range(47,55))}
ITEM_DATA = {
6:("Core Fragment","COMMON",250),7:("Energy Cell","COMMON",300),8:("Steel Chip","COMMON",350),9:("Blue Core","RARE",700),10:("Power Cell","RARE",850),11:("Core Crystal","EPIC",1500),12:("VLDST Blade","LEGENDARY",3500),13:("CORE Overlord","MYTHIC",8000),
14:("Pulse Battery","COMMON",1000),15:("Green Energy","COMMON",1200),16:("Pulse Chip","COMMON",1400),17:("Pulse Core","RARE",2500),18:("Neon Crystal","RARE",3000),19:("Pulse Reactor","EPIC",5500),20:("Pulse Gun","LEGENDARY",12000),21:("PULSE TITAN","MYTHIC",30000),
22:("Aura Shard","COMMON",3000),23:("Blue Gem","COMMON",3500),24:("Aura Crystal","COMMON",5000),25:("Aura Prism","RARE",6500),26:("Sky Core","RARE",7500),27:("Aura Reactor","EPIC",12000),28:("AURA Shield","EPIC",15000),29:("AURA Blade","LEGENDARY",30000),30:("AURA Phantom","MYTHIC",75000),
31:("Void Fragment","COMMON",6000),32:("Dark Energy","COMMON",7000),33:("Void Crystal","RARE",12000),34:("Shadow Core","RARE",15000),35:("Void Reactor","EPIC",25000),36:("Void Shield","EPIC",30000),37:("Void Reaper","LEGENDARY",60000),38:("VOID KING","MYTHIC",150000),
39:("Overdrive Cell","COMMON",12000),40:("Heat Core","COMMON",14000),41:("Overdrive Crystal","RARE",25000),42:("Turbo Core","RARE",33000),43:("Overdrive Reactor","EPIC",50000),44:("Overdrive Gun","EPIC",65000),45:("OVERDRIVE X","LEGENDARY",120000),46:("OVERDRIVE GOD","MYTHIC",280000),
47:("Rift Shard","COMMON",15000),48:("Rift Energy","COMMON",18000),49:("Rift Crystal","RARE",30000),50:("Rift Core","RARE",40000),51:("Rift Reactor","EPIC",65000),52:("Rift Blaster","EPIC",90000),53:("Rift Reaper","LEGENDARY",180000),54:("VLDST RIFT GOD","MYTHIC",500000)
}
WEIGHTS = {"COMMON":15.0,"RARE":10.0,"EPIC":7.5,"LEGENDARY":4.0,"MYTHIC":1.0}
BALANCE_PRODUCTS = {
    "stars_50":(50,50,"50 VLDST Stars","Внутренний баланс ⭐"),
    "stars_100":(100,100,"100 VLDST Stars","Внутренний баланс ⭐"),
    "stars_250":(250,250,"250 VLDST Stars","Внутренний баланс ⭐"),
    "stars_500":(500,500,"500 VLDST Stars","Внутренний баланс ⭐"),
}
STORE_PRODUCTS = {
    "premium_30": {"stars":120,"title":"Premium • 30 дней","description":"Скидка на открытие кейсов + бонус XP","type":"premium","days":30},
    "premium_90": {"stars":300,"title":"Premium • 90 дней","description":"Премиум на 3 месяца","type":"premium","days":90},
    "luck_7": {"stars":80,"title":"LUCK BOOST • 7 дней","description":"Увеличивает шанс редких предметов","type":"luck","days":7},
    "coins_10000": {"stars":50,"title":"10 000 Coins","description":"Мгновенное пополнение Coins","type":"coins","coins":10000},
    "coins_50000": {"stars":180,"title":"50 000 Coins","description":"Выгодный набор Coins","type":"coins","coins":50000},
    "coins_250000": {"stars":700,"title":"250 000 Coins","description":"Максимальный набор Coins","type":"coins","coins":250000},
}

@app.get("/")
def home(): return "VLDST CASE Backend is running!"
@app.get("/health")
def health(): return {"status":"ok","project":"VLDST CASE","version":"ultimate-mobile-v2"}
@app.route("/webapp/<path:filename>")
def webapp(filename): return send_from_directory("webapp", filename)

def db(): return psycopg.connect(DATABASE_URL)

def verify_telegram_init_data(init_data):
    if not init_data: return None
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = data.pop("hash", None)
        if not received_hash: return None
        check = "\n".join(f"{k}={v}" for k,v in sorted(data.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received_hash): return None
        raw = data.get("user")
        return json.loads(raw) if raw else None
    except Exception: return None

def tg_user(): return verify_telegram_init_data(request.headers.get("X-Telegram-Init-Data", ""))
def is_admin():
    u = tg_user()
    return bool(u and int(u.get("id",0)) == ADMIN_ID)

def init_database():
    with db() as conn:
        with conn.cursor() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS users(
                id BIGSERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL, username TEXT, first_name TEXT,
                coins BIGINT NOT NULL DEFAULT 0, stars BIGINT NOT NULL DEFAULT 0, level INTEGER NOT NULL DEFAULT 1,
                xp BIGINT NOT NULL DEFAULT 0, referral_code TEXT UNIQUE, referred_by BIGINT,
                banned BOOLEAN NOT NULL DEFAULT FALSE, premium_until TIMESTAMPTZ, luck_until TIMESTAMPTZ,
                daily_claimed_at TIMESTAMPTZ, game_played_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS cases(
                id BIGSERIAL PRIMARY KEY,name TEXT UNIQUE NOT NULL,description TEXT,price_coins BIGINT NOT NULL DEFAULT 0,
                price_stars INTEGER NOT NULL DEFAULT 0,image_url TEXT,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS items(
                id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,description TEXT,rarity TEXT NOT NULL,
                sell_price BIGINT NOT NULL DEFAULT 0,image_url TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS case_items(
                id BIGSERIAL PRIMARY KEY,case_id BIGINT REFERENCES cases(id) ON DELETE CASCADE,
                item_id BIGINT REFERENCES items(id) ON DELETE CASCADE,drop_chance NUMERIC(10,5) NOT NULL)""")
            c.execute("DELETE FROM case_items a USING case_items b WHERE a.id>b.id AND a.case_id=b.case_id AND a.item_id=b.item_id")
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS case_items_case_item_uidx ON case_items(case_id,item_id)")
            c.execute("""CREATE TABLE IF NOT EXISTS inventory(
                id BIGSERIAL PRIMARY KEY,telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                item_id BIGINT REFERENCES items(id),obtained_from TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS transactions(
                id BIGSERIAL PRIMARY KEY,telegram_id BIGINT,type TEXT NOT NULL,amount BIGINT NOT NULL DEFAULT 0,
                description TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS tasks(
                id BIGSERIAL PRIMARY KEY,title TEXT NOT NULL,description TEXT,reward_coins BIGINT DEFAULT 0,
                reward_stars INTEGER DEFAULT 0,active BOOLEAN DEFAULT TRUE)""")
            c.execute("""CREATE TABLE IF NOT EXISTS task_claims(
                id BIGSERIAL PRIMARY KEY,telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                task_id BIGINT REFERENCES tasks(id) ON DELETE CASCADE,claimed_at TIMESTAMPTZ DEFAULT NOW(),UNIQUE(telegram_id,task_id))""")
            c.execute("""CREATE TABLE IF NOT EXISTS broadcasts(
                id BIGSERIAL PRIMARY KEY,text TEXT NOT NULL,sent INTEGER DEFAULT 0,failed INTEGER DEFAULT 0,created_at TIMESTAMPTZ DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS promo_codes(
                id BIGSERIAL PRIMARY KEY,code TEXT UNIQUE NOT NULL,reward_coins BIGINT DEFAULT 0,reward_stars INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 1,uses INTEGER DEFAULT 0,active BOOLEAN DEFAULT TRUE,created_at TIMESTAMPTZ DEFAULT NOW())""")
            c.execute("""CREATE TABLE IF NOT EXISTS promo_claims(
                id BIGSERIAL PRIMARY KEY,telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                promo_id BIGINT REFERENCES promo_codes(id) ON DELETE CASCADE,created_at TIMESTAMPTZ DEFAULT NOW(),UNIQUE(telegram_id,promo_id))""")
            c.execute("""CREATE TABLE IF NOT EXISTS game_rounds(
                token TEXT PRIMARY KEY,telegram_id BIGINT NOT NULL,secret INTEGER NOT NULL,reward INTEGER NOT NULL,created_at TIMESTAMPTZ DEFAULT NOW())""")
            for col,typ in [("premium_until","TIMESTAMPTZ"),("luck_until","TIMESTAMPTZ"),("daily_claimed_at","TIMESTAMPTZ"),("game_played_at","TIMESTAMPTZ")]:
                c.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}")
            for cid,(name,pc,ps,key) in CASES.items():
                c.execute("""INSERT INTO cases(id,name,description,price_coins,price_stars,image_url,active)
                    VALUES(%s,%s,%s,%s,%s,%s,TRUE) ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,
                    price_coins=EXCLUDED.price_coins,price_stars=EXCLUDED.price_stars,image_url=EXCLUDED.image_url,active=TRUE""",
                    (cid,name,f"{name} — эксклюзивный кейс",pc,ps,f"/webapp/assets/cases/{key}.svg"))
            for iid,(name,rarity,sell_price) in ITEM_DATA.items():
                c.execute("""INSERT INTO items(id,name,description,rarity,sell_price,image_url) VALUES(%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,rarity=EXCLUDED.rarity,
                    sell_price=EXCLUDED.sell_price,image_url=EXCLUDED.image_url""",
                    (iid,name,f"Предмет {name} из VLDST CASE",rarity,sell_price,f"/webapp/assets/items/{iid}.svg"))
            for cid,item_ids in CASE_ITEMS.items():
                for iid in item_ids:
                    c.execute("""INSERT INTO case_items(case_id,item_id,drop_chance) VALUES(%s,%s,%s)
                        ON CONFLICT(case_id,item_id) DO UPDATE SET drop_chance=EXCLUDED.drop_chance""",
                        (cid,iid,WEIGHTS[ITEM_DATA[iid][1]]))
            c.execute("INSERT INTO tasks(title,description,reward_coins,active) SELECT 'Первый запуск','Открой любой кейс',1500,TRUE WHERE NOT EXISTS (SELECT 1 FROM tasks)")
            conn.commit()

def ensure_user(u, referral=None):
    tid=int(u["id"])
    with db() as conn:
        with conn.cursor() as c:
            c.execute("""INSERT INTO users(telegram_id,username,first_name,referral_code,referred_by)
                VALUES(%s,%s,%s,%s,%s) ON CONFLICT(telegram_id) DO UPDATE SET username=EXCLUDED.username,first_name=EXCLUDED.first_name
                RETURNING telegram_id,coins,stars,level,xp,referred_by,banned,premium_until,luck_until""",
                (tid,u.get("username"),u.get("first_name") or "Игрок",f"VLDST{tid}",None))
            row=c.fetchone()
            if referral and referral!=tid and row[5] is None:
                c.execute("SELECT telegram_id FROM users WHERE telegram_id=%s",(referral,))
                if c.fetchone():
                    c.execute("UPDATE users SET referred_by=%s,coins=coins+500 WHERE telegram_id=%s AND referred_by IS NULL",(referral,tid))
                    if c.rowcount:
                        c.execute("UPDATE users SET coins=coins+500 WHERE telegram_id=%s",(referral,))
                        c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'REFERRAL_REWARD',500,'Реферальный бонус'),(%s,'REFERRAL_REWARD',500,'Бонус за приглашение')",(tid,referral))
            conn.commit()
    return row

def choose_item(rows, luck=False):
    weighted=[]
    for r in rows:
        w=float(r[6])
        if luck and r[3] in ("RARE","EPIC","LEGENDARY","MYTHIC"): w*=1.35
        weighted.append((r,w))
    total=sum(x[1] for x in weighted)
    roll=random.uniform(0,total); cur=0
    for r,w in weighted:
        cur+=w
        if roll<=cur:return r
    return weighted[-1][0]

def select_item(case_id, tid=None):
    with db() as conn:
        with conn.cursor() as c:
            c.execute("""SELECT i.id,i.name,i.description,i.rarity,i.sell_price,i.image_url,ci.drop_chance FROM case_items ci
                JOIN items i ON i.id=ci.item_id WHERE ci.case_id=%s""",(case_id,));rows=c.fetchall()
            luck=False
            if tid:
                c.execute("SELECT luck_until FROM users WHERE telegram_id=%s",(tid,));r=c.fetchone();luck=bool(r and r[0] and r[0]>datetime.now(timezone.utc))
    return choose_item(rows,luck)

def telegram_api(method,payload):
    data=urllib.parse.urlencode(payload).encode()
    req=urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}",data=data)
    with urllib.request.urlopen(req,timeout=20) as resp:return json.loads(resp.read().decode())

@app.get("/api/user")
@app.get("/api/me")
def api_me():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    ensure_user(u)
    with db() as conn:
        with conn.cursor() as c:
            c.execute("""SELECT telegram_id,username,first_name,coins,stars,level,xp,referral_code,banned,premium_until,luck_until,
                (SELECT COUNT(*) FROM inventory WHERE telegram_id=users.telegram_id) FROM users WHERE telegram_id=%s""",(int(u["id"]),));r=c.fetchone()
    if not r:return {"error":"user_not_found"},404
    now=datetime.now(timezone.utc)
    premium=bool(r[9] and r[9]>now);luck=bool(r[10] and r[10]>now)
    return {"telegram_id":r[0],"username":r[1],"first_name":r[2],"coins":r[3],"stars":r[4],"level":r[5],"xp":r[6],"referral_code":r[7],"banned":r[8],"premium":premium,"premium_until":r[9].isoformat() if r[9] else None,"luck_boost":luck,"luck_until":r[10].isoformat() if r[10] else None,"inventory_count":r[11]}

@app.get("/api/cases")
def api_cases():
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT id,name,description,price_coins,price_stars,image_url FROM cases WHERE active=TRUE ORDER BY id");rows=c.fetchall()
    return {"cases":[{"id":r[0],"name":r[1],"description":r[2],"price_coins":r[3],"price_stars":r[4],"image_url":r[5]} for r in rows]}

@app.get("/api/cases/<int:case_id>/items")
def api_case_items(case_id):
    with db() as conn:
        with conn.cursor() as c:c.execute("""SELECT i.id,i.name,i.description,i.rarity,i.sell_price,i.image_url,ci.drop_chance FROM case_items ci JOIN items i ON i.id=ci.item_id WHERE ci.case_id=%s ORDER BY ci.drop_chance DESC,i.id""",(case_id,));rows=c.fetchall()
    return {"items":[{"id":r[0],"name":r[1],"description":r[2],"rarity":r[3],"sell_price":r[4],"image_url":r[5],"drop_chance":float(r[6])} for r in rows]}

@app.get("/api/inventory")
def inventory():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    with db() as conn:
        with conn.cursor() as c:c.execute("""SELECT inv.id,i.id,i.name,i.description,i.rarity,i.sell_price,i.image_url,inv.obtained_from,inv.created_at FROM inventory inv JOIN items i ON i.id=inv.item_id WHERE inv.telegram_id=%s ORDER BY inv.created_at DESC""",(int(u["id"]),));rows=c.fetchall()
    return {"inventory":[{"inventory_id":r[0],"item_id":r[1],"name":r[2],"description":r[3],"rarity":r[4],"sell_price":r[5],"image_url":r[6],"obtained_from":r[7],"created_at":r[8].isoformat()} for r in rows]}

@app.post("/api/inventory/<int:iid>/sell")
def sell(iid):
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT i.name,i.sell_price FROM inventory inv JOIN items i ON i.id=inv.item_id WHERE inv.id=%s AND inv.telegram_id=%s FOR UPDATE",(iid,tid));r=c.fetchone()
            if not r:return {"error":"not_found"},404
            c.execute("DELETE FROM inventory WHERE id=%s AND telegram_id=%s",(iid,tid))
            c.execute("UPDATE users SET coins=coins+%s WHERE telegram_id=%s RETURNING coins",(r[1],tid));coins=c.fetchone()[0]
            c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'ITEM_SELL',%s,%s)",(tid,r[1],f"Продажа {r[0]}"));conn.commit()
    return {"success":True,"coins":coins,"sold_for":r[1]}

@app.post("/api/cases/<int:case_id>/open")
def open_case(case_id):
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT coins,banned,premium_until FROM users WHERE telegram_id=%s FOR UPDATE",(tid,));ur=c.fetchone()
            if not ur:return {"error":"user_not_found"},404
            if ur[1]:return {"error":"banned"},403
            c.execute("SELECT name,price_coins FROM cases WHERE id=%s AND active=TRUE",(case_id,));case=c.fetchone()
            if not case:return {"error":"case_not_found"},404
            price=int(case[1]);premium=bool(ur[2] and ur[2]>datetime.now(timezone.utc));price=max(1,int(price*0.9)) if premium else price
            if ur[0]<price:return {"error":"not_enough_coins"},400
            c.execute("SELECT i.id,i.name,i.description,i.rarity,i.sell_price,i.image_url,ci.drop_chance FROM case_items ci JOIN items i ON i.id=ci.item_id WHERE ci.case_id=%s",(case_id,));rows=c.fetchall()
            c.execute("SELECT luck_until FROM users WHERE telegram_id=%s",(tid,));lr=c.fetchone();luck=bool(lr and lr[0] and lr[0]>datetime.now(timezone.utc))
            item=choose_item(rows,luck)
            c.execute("UPDATE users SET coins=coins-%s,xp=xp+10,level=GREATEST(1,FLOOR((xp+10)/100)+1)::INTEGER WHERE telegram_id=%s RETURNING coins,xp,level",(price,tid));coins,xp,level=c.fetchone()
            c.execute("INSERT INTO inventory(telegram_id,item_id,obtained_from) VALUES(%s,%s,%s)",(tid,item[0],f"case:{case_id}"))
            c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'CASE_OPEN',%s,%s)",(tid,-price,f"Открытие {case[0]}"));conn.commit()
    return {"success":True,"coins":coins,"xp":xp,"level":level,"discount":premium,"item":{"id":item[0],"name":item[1],"description":item[2],"rarity":item[3],"sell_price":item[4],"image_url":item[5]}}

@app.get("/api/shop")
def shop():
    return {"balance_products":[{"id":k,"stars":v[0],"charge":v[1],"title":v[2],"description":v[3],"type":"balance"} for k,v in BALANCE_PRODUCTS.items()],"store_products":[{"id":k,**v} for k,v in STORE_PRODUCTS.items()]}

@app.post("/api/stars/invoice")
def stars_invoice():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    data=request.get_json(silent=True) or {};kind=data.get("kind","balance")
    if kind=="balance":
        product=data.get("product","stars_100")
        if product not in BALANCE_PRODUCTS:return {"error":"bad_product"},400
        stars,charge,title,desc=BALANCE_PRODUCTS[product];amount=stars;payload=f"balance:{u['id']}:{stars}:{int(time.time())}"
    elif kind=="store":
        product=data.get("product")
        if product not in STORE_PRODUCTS:return {"error":"bad_product"},400
        p=STORE_PRODUCTS[product];title=p["title"];desc=p["description"];amount=p["stars"];payload=f"store:{u['id']}:{product}:{int(time.time())}"
    elif kind=="case":
        cid=int(data.get("case_id",0))
        if cid not in CASES:return {"error":"bad_case"},400
        title=CASES[cid][0];desc=f"Открытие кейса {title}";amount=CASES[cid][2];payload=f"case:{u['id']}:{cid}:{int(time.time())}"
    else:return {"error":"bad_kind"},400
    res=telegram_api("createInvoiceLink",{"title":title[:32],"description":desc[:255],"payload":payload,"currency":"XTR","prices":json.dumps([{"label":title[:32],"amount":int(amount)}])})
    if not res.get("ok"):return {"error":"telegram_invoice_error","details":res},500
    return {"invoice_url":res["result"],"stars":amount}

@app.get("/api/referrals")
def referrals():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM users WHERE referred_by=%s",(tid,));count=c.fetchone()[0]
            c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE telegram_id=%s AND type='REFERRAL_REWARD'",(tid,));earned=c.fetchone()[0]
    return {"referral_link":f"https://t.me/{BOT_USERNAME}?start=ref_{tid}","count":count,"earned":earned,"reward":500}

@app.get("/api/leaderboard")
def leaderboard():
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT telegram_id,username,first_name,level,xp,coins FROM users WHERE banned=FALSE ORDER BY level DESC,xp DESC,coins DESC LIMIT 100");rows=c.fetchall()
    return {"leaderboard":[{"rank":i+1,"telegram_id":r[0],"username":r[1],"first_name":r[2],"level":r[3],"xp":r[4],"coins":r[5]} for i,r in enumerate(rows)]}

@app.get("/api/tasks")
def tasks():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    with db() as conn:
        with conn.cursor() as c:c.execute("""SELECT t.id,t.title,t.description,t.reward_coins,t.reward_stars,EXISTS(SELECT 1 FROM task_claims x WHERE x.task_id=t.id AND x.telegram_id=%s) FROM tasks t WHERE t.active=TRUE ORDER BY t.id""",(int(u["id"]),));rows=c.fetchall()
    return {"tasks":[{"id":r[0],"title":r[1],"description":r[2],"reward_coins":r[3],"reward_stars":r[4],"claimed":r[5]} for r in rows]}

@app.post("/api/tasks/<int:task_id>/claim")
def claim_task(task_id):
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"])
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT reward_coins,reward_stars FROM tasks WHERE id=%s AND active=TRUE",(task_id,));t=c.fetchone()
            if not t:return {"error":"task_not_found"},404
            try:c.execute("INSERT INTO task_claims(telegram_id,task_id) VALUES(%s,%s)",(tid,task_id))
            except psycopg.errors.UniqueViolation: conn.rollback();return {"error":"already_claimed"},400
            c.execute("UPDATE users SET coins=coins+%s,stars=stars+%s WHERE telegram_id=%s RETURNING coins,stars",(t[0],t[1],tid));r=c.fetchone();conn.commit()
    return {"success":True,"coins":r[0],"stars":r[1]}

@app.post("/api/daily-bonus")
def daily_bonus():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"]);now=datetime.now(timezone.utc)
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT daily_claimed_at,banned FROM users WHERE telegram_id=%s FOR UPDATE",(tid,));r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            if r[1]:return {"error":"banned"},403
            if r[0] and now-r[0] < timedelta(hours=20):return {"error":"already_claimed","next":"20h"},400
            reward=random.randint(500,1500);c.execute("UPDATE users SET coins=coins+%s,daily_claimed_at=NOW() WHERE telegram_id=%s RETURNING coins",(reward,tid));coins=c.fetchone()[0]
            c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'DAILY_BONUS',%s,'Ежедневный бонус')",(tid,reward));conn.commit()
    return {"success":True,"reward":reward,"coins":coins}

@app.post("/api/minigame/start")
def game_start():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    tid=int(u["id"]);now=datetime.now(timezone.utc)
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT game_played_at,banned FROM users WHERE telegram_id=%s FOR UPDATE",(tid,));r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            if r[1]:return {"error":"banned"},403
            if r[0] and now-r[0] < timedelta(minutes=2):return {"error":"cooldown","seconds":max(1,int(120-(now-r[0]).total_seconds()))},400
            secret=random.randint(1,3);token=hashlib.sha256(f"{tid}:{secret}:{int(time.time())}:{random.random()}".encode()).hexdigest()[:24]
            c.execute("UPDATE users SET game_played_at=NOW() WHERE telegram_id=%s",(tid,));conn.commit()
    with db() as conn:
        with conn.cursor() as c:c.execute("CREATE TABLE IF NOT EXISTS game_rounds(token TEXT PRIMARY KEY,telegram_id BIGINT NOT NULL,secret INTEGER NOT NULL,reward INTEGER NOT NULL,created_at TIMESTAMPTZ DEFAULT NOW())")
        c.execute("INSERT INTO game_rounds(token,telegram_id,secret,reward) VALUES(%s,%s,%s,%s)",(token,tid,secret,random.randint(700,4500)));conn.commit()
    return {"token":token,"choices":[1,2,3],"message":"Выбери один из трёх энергетических модулей. Один даст награду."}

@app.post("/api/minigame/choose")
def game_choose():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    d=request.get_json(silent=True) or {};token=str(d.get("token",""));choice=int(d.get("choice",0));tid=int(u["id"])
    if choice not in (1,2,3):return {"error":"bad_choice"},400
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT secret,reward FROM game_rounds WHERE token=%s AND telegram_id=%s",(token,tid));r=c.fetchone()
            if not r:return {"error":"round_not_found"},404
            reward=r[1] if choice==r[0] else max(100,int(r[1]*0.15))
            c.execute("DELETE FROM game_rounds WHERE token=%s",(token,));c.execute("UPDATE users SET coins=coins+%s,xp=xp+5 WHERE telegram_id=%s RETURNING coins,xp",(reward,tid));coins,xp=c.fetchone();c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'MINIGAME',%s,'VLDST RUSH')",(tid,reward));conn.commit()
    return {"success":True,"win":choice==r[0],"reward":reward,"coins":coins,"xp":xp}

@app.post("/api/promo/redeem")
def redeem_promo():
    u=tg_user()
    if not u:return {"error":"unauthorized"},401
    code=str((request.get_json(silent=True) or {}).get("code","" )).strip().upper()
    if not code:return {"error":"code_required"},400
    tid=int(u["id"])
    with db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT id,reward_coins,reward_stars,max_uses,uses,active FROM promo_codes WHERE code=%s FOR UPDATE",(code,));p=c.fetchone()
            if not p or not p[5] or p[4]>=p[3]:return {"error":"invalid_code"},400
            try:c.execute("INSERT INTO promo_claims(telegram_id,promo_id) VALUES(%s,%s)",(tid,p[0]))
            except psycopg.errors.UniqueViolation:conn.rollback();return {"error":"already_used"},400
            c.execute("UPDATE promo_codes SET uses=uses+1 WHERE id=%s",(p[0],));c.execute("UPDATE users SET coins=coins+%s,stars=stars+%s WHERE telegram_id=%s RETURNING coins,stars",(p[1],p[2],tid));r=c.fetchone();conn.commit()
    return {"success":True,"coins":r[0],"stars":r[1]}

@app.get("/api/admin/check")
def admin_check(): return {"admin":is_admin()}
@app.get("/api/admin/stats")
def admin_stats():
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:
            out={}
            for t in ("users","cases","items","inventory","transactions","broadcasts","promo_codes"):
                c.execute(f"SELECT COUNT(*) FROM {t}");out[t]=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE banned=TRUE");out["banned_users"]=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE premium_until>NOW()");out["premium_users"]=c.fetchone()[0]
            c.execute("SELECT COALESCE(SUM(coins),0),COALESCE(SUM(stars),0) FROM users");out["coins"],out["stars"]=c.fetchone()
    return out
@app.get("/api/admin/users")
def admin_users():
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT telegram_id,username,first_name,coins,stars,level,xp,banned,premium_until,luck_until,created_at FROM users ORDER BY created_at DESC LIMIT 500");rows=c.fetchall()
    return {"users":[{"telegram_id":r[0],"username":r[1],"first_name":r[2],"coins":r[3],"stars":r[4],"level":r[5],"xp":r[6],"banned":r[7],"premium":bool(r[8] and r[8]>datetime.now(timezone.utc)),"premium_until":r[8].isoformat() if r[8] else None,"luck_boost":bool(r[9] and r[9]>datetime.now(timezone.utc)),"created_at":r[10].isoformat()} for r in rows]}
@app.post("/api/admin/user/<int:tid>/ban")
def ban_user(tid):
    if not is_admin():return {"error":"forbidden"},403
    banned=bool((request.get_json(silent=True) or {}).get("banned",True))
    with db() as conn:
        with conn.cursor() as c:c.execute("UPDATE users SET banned=%s WHERE telegram_id=%s",(banned,tid));conn.commit()
    return {"success":True,"banned":banned}
@app.post("/api/admin/give-coins")
def give_coins():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {};tid=int(d.get("telegram_id"));amount=int(d.get("amount"))
    with db() as conn:
        with conn.cursor() as c:
            c.execute("UPDATE users SET coins=coins+%s WHERE telegram_id=%s RETURNING coins",(amount,tid));r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'ADMIN_GIVE_COINS',%s,'Админ выдал Coins')",(tid,amount));conn.commit()
    return {"success":True,"coins":r[0]}
@app.post("/api/admin/give-stars")
def give_stars():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {};tid=int(d.get("telegram_id"));amount=int(d.get("amount"))
    with db() as conn:
        with conn.cursor() as c:
            c.execute("UPDATE users SET stars=stars+%s WHERE telegram_id=%s RETURNING stars",(amount,tid));r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'ADMIN_GIVE_STARS',%s,'Админ выдал Stars')",(tid,amount));conn.commit()
    return {"success":True,"stars":r[0]}
@app.post("/api/admin/user/<int:tid>/premium")
def admin_premium(tid):
    if not is_admin():return {"error":"forbidden"},403
    days=max(1,int((request.get_json(silent=True) or {}).get("days",30)));now=datetime.now(timezone.utc)
    with db() as conn:
        with conn.cursor() as c:
            c.execute("UPDATE users SET premium_until=GREATEST(COALESCE(premium_until,NOW()),NOW())+make_interval(days=>%s) WHERE telegram_id=%s RETURNING premium_until",(days,tid));r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            conn.commit()
    return {"success":True,"premium_until":r[0].isoformat()}
@app.post("/api/admin/user/<int:tid>/luck")
def admin_luck(tid):
    if not is_admin():return {"error":"forbidden"},403
    days=max(1,int((request.get_json(silent=True) or {}).get("days",7)))
    with db() as conn:
        with conn.cursor() as c:
            c.execute("UPDATE users SET luck_until=GREATEST(COALESCE(luck_until,NOW()),NOW())+make_interval(days=>%s) WHERE telegram_id=%s RETURNING luck_until",(days,tid));r=c.fetchone()
            if not r:return {"error":"user_not_found"},404
            conn.commit()
    return {"success":True,"luck_until":r[0].isoformat()}
@app.post("/api/admin/user/<int:tid>/reset")
def admin_reset(tid):
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:c.execute("UPDATE users SET coins=0,stars=0,level=1,xp=0 WHERE telegram_id=%s",(tid,));conn.commit()
    return {"success":True}
@app.post("/api/admin/broadcast")
def broadcast():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {};text=str(d.get("text","" )).strip()
    if not text:return {"error":"text_required"},400
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT telegram_id FROM users WHERE banned=FALSE");ids=[r[0] for r in c.fetchall()]
    sent=failed=0
    for tid in ids:
        try:telegram_api("sendMessage",{"chat_id":tid,"text":text,"parse_mode":"HTML","disable_web_page_preview":"true"});sent+=1
        except Exception:failed+=1
    with db() as conn:
        with conn.cursor() as c:c.execute("INSERT INTO broadcasts(text,sent,failed) VALUES(%s,%s,%s)",(text,sent,failed));conn.commit()
    return {"success":True,"sent":sent,"failed":failed}
@app.get("/api/admin/broadcasts")
def admin_broadcasts():
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT id,text,sent,failed,created_at FROM broadcasts ORDER BY id DESC LIMIT 30");rows=c.fetchall()
    return {"broadcasts":[{"id":r[0],"text":r[1],"sent":r[2],"failed":r[3],"created_at":r[4].isoformat()} for r in rows]}
@app.get("/api/admin/cases")
def admin_cases():
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT id,name,price_coins,price_stars,image_url,active FROM cases ORDER BY id");rows=c.fetchall()
    return {"cases":[{"id":r[0],"name":r[1],"price_coins":r[2],"price_stars":r[3],"image_url":r[4],"active":r[5]} for r in rows]}
@app.post("/api/admin/cases/<int:cid>/toggle")
def toggle_case(cid):
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:c.execute("UPDATE cases SET active=NOT active WHERE id=%s RETURNING active",(cid,));r=c.fetchone();conn.commit()
    return {"success":True,"active":r[0] if r else None}
@app.get("/api/admin/items")
def admin_items():
    if not is_admin():return {"error":"forbidden"},403
    with db() as conn:
        with conn.cursor() as c:c.execute("SELECT id,name,rarity,sell_price,image_url FROM items ORDER BY id");rows=c.fetchall()
    return {"items":[{"id":r[0],"name":r[1],"rarity":r[2],"sell_price":r[3],"image_url":r[4]} for r in rows]}
@app.get("/api/admin/products")
def admin_products():
    if not is_admin():return {"error":"forbidden"},403
    return {"products":[{"id":k,**v} for k,v in STORE_PRODUCTS.items()]}
@app.post("/api/admin/task")
def admin_task_create():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {}
    title=str(d.get("title","" )).strip();desc=str(d.get("description","" )).strip();coins=int(d.get("reward_coins",0));stars=int(d.get("reward_stars",0))
    if not title:return {"error":"title_required"},400
    with db() as conn:
        with conn.cursor() as c:c.execute("INSERT INTO tasks(title,description,reward_coins,reward_stars) VALUES(%s,%s,%s,%s) RETURNING id",(title,desc,coins,stars));rid=c.fetchone()[0];conn.commit()
    return {"success":True,"id":rid}
@app.post("/api/admin/promo")
def admin_promo_create():
    if not is_admin():return {"error":"forbidden"},403
    d=request.get_json(silent=True) or {};code=str(d.get("code","" )).strip().upper();coins=int(d.get("reward_coins",0));stars=int(d.get("reward_stars",0));max_uses=max(1,int(d.get("max_uses",1)))
    if not code:return {"error":"code_required"},400
    with db() as conn:
        with conn.cursor() as c:
            try:c.execute("INSERT INTO promo_codes(code,reward_coins,reward_stars,max_uses) VALUES(%s,%s,%s,%s) RETURNING id",(code,coins,stars,max_uses));rid=c.fetchone()[0]
            except psycopg.errors.UniqueViolation:conn.rollback();return {"error":"code_exists"},400
            conn.commit()
    return {"success":True,"id":rid}

async def payment_success(message: Message):
    sp=message.successful_payment;payload=sp.invoice_payload.split(":");tid=message.from_user.id
    if not payload:return
    kind=payload[0]
    if kind=="balance":
        stars=int(payload[2])
        with db() as conn:
            with conn.cursor() as c:c.execute("UPDATE users SET stars=stars+%s WHERE telegram_id=%s RETURNING stars",(stars,tid));new=c.fetchone()[0];c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'STAR_PURCHASE',%s,'Покупка Stars через Telegram')",(tid,stars));conn.commit()
        await message.answer(f"⭐ Оплата успешна!\nЗачислено: {stars} Stars.\nБаланс: {new} ⭐")
    elif kind=="case":
        cid=int(payload[2])
        with db() as conn:
            with conn.cursor() as c:
                c.execute("SELECT price_stars,name FROM cases WHERE id=%s AND active=TRUE",(cid,));case=c.fetchone();c.execute("SELECT banned,luck_until FROM users WHERE telegram_id=%s",(tid,));ban=c.fetchone()
                if not case or not ban or ban[0]:return
                c.execute("SELECT i.id,i.name,i.description,i.rarity,i.sell_price,i.image_url,ci.drop_chance FROM case_items ci JOIN items i ON i.id=ci.item_id WHERE ci.case_id=%s",(cid,));rows=c.fetchall();item=choose_item(rows,bool(ban[1] and ban[1]>datetime.now(timezone.utc)))
                c.execute("INSERT INTO inventory(telegram_id,item_id,obtained_from) VALUES(%s,%s,%s)",(tid,item[0],f"stars_case:{cid}"));c.execute("UPDATE users SET xp=xp+10,level=GREATEST(1,FLOOR((xp+10)/100)+1)::INTEGER WHERE telegram_id=%s",(tid));c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'CASE_STARS_OPEN',%s,%s)",(tid,-case[0],f"Открытие {case[1]} за Stars"));conn.commit()
        await message.answer(f"🎉 Кейс открыт!\n\n💎 {item[1]}\nРедкость: {item[3]}\n💰 Продажа: {item[4]:,} Coins")
    elif kind=="store":
        product=payload[2];p=STORE_PRODUCTS.get(product)
        if not p:return
        with db() as conn:
            with conn.cursor() as c:
                if p["type"]=="premium":c.execute("UPDATE users SET premium_until=GREATEST(COALESCE(premium_until,NOW()),NOW())+make_interval(days=>%s) WHERE telegram_id=%s",(p["days"],tid))
                elif p["type"]=="luck":c.execute("UPDATE users SET luck_until=GREATEST(COALESCE(luck_until,NOW()),NOW())+make_interval(days=>%s) WHERE telegram_id=%s",(p["days"],tid))
                elif p["type"]=="coins":c.execute("UPDATE users SET coins=coins+%s WHERE telegram_id=%s",(p["coins"],tid))
                c.execute("INSERT INTO transactions(telegram_id,type,amount,description) VALUES(%s,'STORE_PURCHASE',%s,%s)",(tid,-p["stars"],p["title"]));conn.commit()
        await message.answer(f"✅ Покупка выполнена!\n{p['title']}")

bot=Bot(TOKEN);dp=Dispatcher()
@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id!=ADMIN_ID:return await message.answer("⛔ Доступ запрещён.")
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚙️ Открыть админ-панель",web_app=WebAppInfo(url=ADMIN_URL))]])
    await message.answer("🛠 <b>VLDST ADMIN</b>\n\nПользователи, бан, Coins, Stars, Premium, реклама, задания, промокоды, кейсы и статистика.",reply_markup=kb,parse_mode="HTML")
@dp.message(Command("start"))
async def start(message: Message):
    u=message.from_user;ref=None;parts=message.text.split(maxsplit=1)
    if len(parts)>1 and parts[1].startswith("ref_"):
        try:ref=int(parts[1][4:])
        except:pass
    row=ensure_user({"id":u.id,"username":u.username,"first_name":u.first_name},ref)
    if row[6]:return await message.answer("⛔ Ваш аккаунт заблокирован.")
    buttons=[[InlineKeyboardButton(text="🎁 Открыть VLDST CASE",web_app=WebAppInfo(url=WEBAPP_URL))]]
    if u.id==ADMIN_ID:buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель",web_app=WebAppInfo(url=ADMIN_URL))])
    await message.answer(f"🌌 <b>VLDST CASE</b>\n\nДобро пожаловать, <b>{html.escape(u.first_name or 'Игрок')}</b>!\n\n🪙 Coins: <b>{row[1]:,}</b>\n⭐ Stars: <b>{row[2]}</b>\n🏆 Уровень: <b>{row[3]}</b>\n⚡ XP: <b>{row[4]}</b>",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),parse_mode="HTML")
@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery): await q.answer(ok=True)
@dp.message(F.successful_payment)
async def success_payment(message: Message): await payment_success(message)

def run_web(): app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")),threaded=True)
async def main():
    init_database();print("VLDST CASE ULTIMATE V2: database ready");Thread(target=run_web,daemon=True).start();await dp.start_polling(bot)
if __name__=="__main__": asyncio.run(main())
