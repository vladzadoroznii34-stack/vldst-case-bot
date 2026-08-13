import os, asyncio, threading, secrets, time, hashlib, hmac, json, base64
from datetime import datetime, timezone
from urllib.parse import parse_qsl
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
import psycopg
from psycopg.rows import dict_row
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv()
BOT_TOKEN=os.getenv('BOT_TOKEN','').strip(); DATABASE_URL=os.getenv('DATABASE_URL','').strip(); WEBAPP_URL=os.getenv('WEBAPP_URL','').strip().rstrip('/')
# Accept both https://domain and accidental https://domain/webapp values.
for _suffix in ('/webapp','/admin'):
    if WEBAPP_URL.endswith(_suffix):
        WEBAPP_URL=WEBAPP_URL[:-len(_suffix)].rstrip('/')
        break
ADMIN_IDS={int(x.strip()) for x in os.getenv('ADMIN_IDS','').split(',') if x.strip().isdigit()}
if not BOT_TOKEN: raise RuntimeError('BOT_TOKEN is missing')
if not DATABASE_URL: raise RuntimeError('DATABASE_URL is missing')
if not WEBAPP_URL.startswith('https://'): raise RuntimeError('WEBAPP_URL must start with https://')
BASE=os.path.dirname(os.path.abspath(__file__)); WEB_DIR=os.path.join(BASE,'webapp'); app=Flask(__name__); BOT_LOOP=None; bot_instance=None

def db(): return psycopg.connect(DATABASE_URL,row_factory=dict_row,connect_timeout=10)
def now(): return datetime.now(timezone.utc)

def svg_data(title, subtitle, color):
    def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800"><defs><radialGradient id="g"><stop stop-color="{color}" stop-opacity=".9"/><stop offset="1" stop-color="#070811"/></radialGradient></defs><rect width="800" height="800" rx="80" fill="#070811"/><circle cx="650" cy="140" r="260" fill="url(#g)"/><circle cx="150" cy="700" r="220" fill="{color}" opacity=".12"/><rect x="55" y="55" width="690" height="690" rx="55" fill="#111322" stroke="{color}" stroke-width="5"/><circle cx="400" cy="320" r="125" fill="#090a12" stroke="{color}" stroke-width="8"/><text x="400" y="342" text-anchor="middle" font-family="Arial" font-size="58" font-weight="900" fill="#fff">VLDST</text><text x="400" y="470" text-anchor="middle" font-family="Arial" font-size="50" font-weight="900" fill="{color}">{esc(title)}</text><text x="400" y="515" text-anchor="middle" font-family="Arial" font-size="25" fill="#c8c9d9">{esc(subtitle)}</text><text x="400" y="690" text-anchor="middle" font-family="Arial" font-size="20" fill="#888aa5">VLDST CASE</text></svg>'''
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()

def init_db():
    schema='''CREATE TABLE IF NOT EXISTS users(id BIGSERIAL PRIMARY KEY,telegram_id BIGINT UNIQUE NOT NULL,username TEXT,first_name TEXT NOT NULL DEFAULT 'Игрок',coins BIGINT NOT NULL DEFAULT 1000,stars BIGINT NOT NULL DEFAULT 0,xp BIGINT NOT NULL DEFAULT 0,level INT NOT NULL DEFAULT 1,premium_until TIMESTAMPTZ,banned BOOLEAN NOT NULL DEFAULT FALSE,referred_by BIGINT,daily_claimed_at TIMESTAMPTZ,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS cases(id SERIAL PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',image_url TEXT NOT NULL,price_coins BIGINT NOT NULL DEFAULT 1000,price_stars INT NOT NULL DEFAULT 10,active BOOLEAN NOT NULL DEFAULT TRUE);
CREATE TABLE IF NOT EXISTS items(id SERIAL PRIMARY KEY,case_id INT REFERENCES cases(id) ON DELETE CASCADE,name TEXT NOT NULL,rarity TEXT NOT NULL DEFAULT 'common',image_url TEXT NOT NULL,sell_price BIGINT NOT NULL DEFAULT 100,weight NUMERIC NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS inventory(id BIGSERIAL PRIMARY KEY,user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,item_id INT REFERENCES items(id),created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),sold_at TIMESTAMPTZ);
CREATE TABLE IF NOT EXISTS tasks(id SERIAL PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',reward_coins BIGINT NOT NULL DEFAULT 0,reward_stars INT NOT NULL DEFAULT 0,active BOOLEAN NOT NULL DEFAULT TRUE);
CREATE TABLE IF NOT EXISTS task_claims(user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,task_id INT REFERENCES tasks(id) ON DELETE CASCADE,claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),PRIMARY KEY(user_id,task_id));
CREATE TABLE IF NOT EXISTS boosts(id BIGSERIAL PRIMARY KEY,user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,type TEXT NOT NULL,expires_at TIMESTAMPTZ NOT NULL);
CREATE TABLE IF NOT EXISTS payments(id BIGSERIAL PRIMARY KEY,telegram_id BIGINT NOT NULL,payload TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,product_id TEXT,amount INT NOT NULL,status TEXT NOT NULL DEFAULT 'created',created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());'''
    with db() as con:
        with con.cursor() as cur:
            cur.execute(schema)
            cur.execute('SELECT COUNT(*) n FROM cases')
            if cur.fetchone()['n']==0: seed(con)
            cur.execute('SELECT COUNT(*) n FROM tasks')
            if cur.fetchone()['n']==0:
                cur.executemany('INSERT INTO tasks(title,description,reward_coins,reward_stars) VALUES(%s,%s,%s,%s)',[('Первый вход','Зайди в VLDST CASE.',500,0),('Собери 3 предмета','Открывай кейсы.',1500,0),('Игрок дня','Сыграй в VLDST RUSH.',750,0)])
        con.commit()

def seed(con):
    cases=[('NEON','Неоновый кейс','#8b5cf6',1000,10),('VOID','Тёмная коллекция','#38bdf8',2500,20),('PHANTOM','Призрачные предметы','#a855f7',5000,35),('ROYAL','Королевская серия','#f59e0b',10000,60),('MYTHIC','Мифические награды','#ef4444',25000,120),('VLDST','Эксклюзивный кейс','#22d3ee',50000,200)]
    with con.cursor() as cur:
        for name,desc,color,coins,stars in cases:
            cur.execute('INSERT INTO cases(name,description,image_url,price_coins,price_stars) VALUES(%s,%s,%s,%s,%s) RETURNING id',(name,desc,svg_data(name,'CASE',color),coins,stars)); cid=cur.fetchone()['id']
            for rar,cls,col,w,sell in [('Common','common','#64748b',45,max(50,coins//20)),('Rare','rare','#3b82f6',28,max(100,coins//10)),('Epic','epic','#a855f7',15,max(250,coins//4)),('Legendary','legendary','#f97316',8,max(700,coins//2)),('Mythic','mythic','#facc15',4,max(1500,coins))]:
                n=f'{name} {rar}'; cur.execute('INSERT INTO items(case_id,name,rarity,image_url,sell_price,weight) VALUES(%s,%s,%s,%s,%s,%s)',(cid,n,cls,svg_data(n,rar.upper(),col),sell,w))

def validate(init_data):
    if not init_data:return None
    try:
        p=dict(parse_qsl(init_data,keep_blank_values=True)); received=p.pop('hash',None)
        if not received:return None
        if time.time()-int(p.get('auth_date','0'))>86400:return None
        check='\n'.join(f'{k}={v}' for k,v in sorted(p.items())); secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest(); calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc,received):return None
        u=json.loads(p.get('user','{}')); return u if u.get('id') else None
    except Exception:return None

def current_user():
    u=validate(request.headers.get('X-Telegram-Init-Data',''))
    if not u:return None
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE telegram_id=%s',(u['id'],)); row=cur.fetchone()
            if not row:
                cur.execute('INSERT INTO users(telegram_id,username,first_name) VALUES(%s,%s,%s) RETURNING *',(u['id'],u.get('username'),u.get('first_name') or 'Игрок')); row=cur.fetchone()
            else:
                cur.execute('UPDATE users SET username=%s,first_name=%s WHERE telegram_id=%s RETURNING *',(u.get('username'),u.get('first_name') or 'Игрок',u['id'])); row=cur.fetchone()
        con.commit()
    return row

def require_user():
    u=current_user()
    if not u:return None,(jsonify(error='unauthorized'),401)
    if u['banned']:return None,(jsonify(error='banned'),403)
    return u,None

def require_admin():
    u,e=require_user()
    if e:return None,e
    if u['telegram_id'] not in ADMIN_IDS:return None,(jsonify(error='admin_required'),403)
    return u,None

def uj(u):
    return {'telegram_id':u['telegram_id'],'username':u['username'],'first_name':u['first_name'],'coins':u['coins'],'stars':u['stars'],'xp':u['xp'],'level':u['level'],'premium_until':u['premium_until'].isoformat() if u['premium_until'] else None,'banned':u['banned']}

@app.get('/health')
def health():return jsonify(ok=True)
@app.get('/webapp')
@app.get('/webapp/')
def webapp_index():
    return send_from_directory(WEB_DIR,'index.html')

@app.get('/webapp/<path:filename>')
def wf(filename):return send_from_directory(WEB_DIR,filename)

@app.get('/index.html')
def index_alias():return send_from_directory(WEB_DIR,'index.html')

@app.get('/')
def home():return send_from_directory(WEB_DIR,'index.html')
@app.get('/admin')
def admin():return send_from_directory(WEB_DIR,'admin.html')
@app.get('/api/user')
def api_user():
    u,e=require_user(); return e or jsonify(uj(u))
@app.get('/api/cases')
def api_cases():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT * FROM cases WHERE active ORDER BY id'); rows=cur.fetchall()
    return jsonify(cases=[dict(r) for r in rows])
@app.get('/api/cases/<int:cid>/items')
def api_items(cid):
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT * FROM items WHERE case_id=%s ORDER BY id',(cid,));rows=cur.fetchall()
    return jsonify(items=[dict(r) for r in rows])

def pick(cur,cid):
    cur.execute('SELECT * FROM items WHERE case_id=%s',(cid,)); items=cur.fetchall(); total=sum(float(i['weight']) for i in items)
    if not items:return None
    x=secrets.SystemRandom().random()*total; acc=0
    for i in items:
        acc+=float(i['weight'])
        if x<=acc:return i
    return items[-1]
@app.post('/api/cases/<int:cid>/open')
def open_case(cid):
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT * FROM cases WHERE id=%s AND active FOR UPDATE',(cid,)); c=cur.fetchone()
            if not c:return jsonify(error='case_not_found'),404
            if u['coins']<c['price_coins']:return jsonify(error='not_enough_coins'),400
            item=pick(cur,cid)
            if not item:return jsonify(error='case_has_no_items'),400
            cur.execute('UPDATE users SET coins=coins-%s,xp=xp+10 WHERE telegram_id=%s RETURNING *',(c['price_coins'],u['telegram_id'])); nu=cur.fetchone()
            cur.execute('INSERT INTO inventory(user_id,item_id) VALUES(%s,%s)',(nu['id'],item['id']));con.commit()
    return jsonify(item=dict(item),user=uj(nu))
@app.get('/api/inventory')
def inventory():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('''SELECT i.id inventory_id,it.id,it.name,it.rarity,it.image_url,it.sell_price FROM inventory i JOIN users u ON u.id=i.user_id JOIN items it ON it.id=i.item_id WHERE u.telegram_id=%s AND i.sold_at IS NULL ORDER BY i.id DESC''',(u['telegram_id'],));rows=cur.fetchall()
    return jsonify(inventory=[dict(r) for r in rows])
@app.post('/api/inventory/<int:iid>/sell')
def sell(iid):
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT i.id,it.sell_price FROM inventory i JOIN users u ON u.id=i.user_id JOIN items it ON it.id=i.item_id WHERE i.id=%s AND u.telegram_id=%s AND i.sold_at IS NULL FOR UPDATE''',(iid,u['telegram_id']));r=cur.fetchone()
            if not r:return jsonify(error='item_not_found'),404
            cur.execute('UPDATE inventory SET sold_at=NOW() WHERE id=%s',(iid,));cur.execute('UPDATE users SET coins=coins+%s WHERE telegram_id=%s RETURNING coins',(r['sell_price'],u['telegram_id']));coins=cur.fetchone()['coins'];con.commit()
    return jsonify(sold_for=r['sell_price'],coins=coins)
@app.post('/api/daily')
def daily():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT daily_claimed_at FROM users WHERE telegram_id=%s FOR UPDATE',(u['telegram_id'],));last=cur.fetchone()['daily_claimed_at']
            if last and last.astimezone(timezone.utc).date()==now().date():return jsonify(error='already_claimed'),400
            cur.execute('UPDATE users SET coins=coins+1000,daily_claimed_at=NOW(),xp=xp+25 WHERE telegram_id=%s RETURNING *',(u['telegram_id'],));nu=cur.fetchone();con.commit()
    return jsonify(reward=1000,user=uj(nu))
@app.get('/api/referrals')
def refs():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT COUNT(*) n FROM users WHERE referred_by=%s',(u['telegram_id'],));n=cur.fetchone()['n']
    return jsonify(count=n,earned=n*500,referral_link=f'https://t.me/{os.getenv("BOT_USERNAME","VLDST_CASE_BOT")}?start=ref_{u["telegram_id"]}')
@app.get('/api/tasks')
def tasks():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT t.*,EXISTS(SELECT 1 FROM task_claims tc WHERE tc.task_id=t.id AND tc.user_id=%s) claimed FROM tasks t WHERE t.active ORDER BY t.id',(u['id'],));rows=cur.fetchall()
    return jsonify(tasks=[dict(r) for r in rows])
@app.post('/api/tasks/<int:tid>/claim')
def claim(tid):
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT * FROM tasks WHERE id=%s AND active',(tid,));t=cur.fetchone()
            if not t:return jsonify(error='task_not_found'),404
            cur.execute('SELECT 1 FROM task_claims WHERE user_id=%s AND task_id=%s',(u['id'],tid))
            if cur.fetchone():return jsonify(error='already_claimed'),400
            cur.execute('INSERT INTO task_claims(user_id,task_id) VALUES(%s,%s)',(u['id'],tid));cur.execute('UPDATE users SET coins=coins+%s,stars=stars+%s,xp=xp+50 WHERE id=%s',(t['reward_coins'],t['reward_stars'],u['id']));con.commit()
    return jsonify(ok=True)
@app.post('/api/minigame/play')
def mini():
    u,e=require_user()
    if e:return e
    score=secrets.randbelow(100)+1; reward=min(1000,100+score*5)
    with db() as con:
        with con.cursor() as cur:cur.execute('UPDATE users SET coins=coins+%s,xp=xp+%s WHERE id=%s RETURNING *',(reward,max(5,score//5),u['id']));nu=cur.fetchone();con.commit()
    return jsonify(score=score,reward=reward,user=uj(nu))
@app.get('/api/leaderboard')
def leaderboard():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT first_name,username,level,xp FROM users WHERE banned=FALSE ORDER BY xp DESC,level DESC LIMIT 50');rows=cur.fetchall()
    return jsonify(leaderboard=[dict(r) for r in rows])
@app.get('/api/boosts')
def boosts():
    u,e=require_user()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('DELETE FROM boosts WHERE expires_at<=NOW()');cur.execute('SELECT type,expires_at FROM boosts WHERE user_id=%s ORDER BY expires_at',(u['id'],));rows=cur.fetchall();con.commit()
    return jsonify(boosts=[dict(r) for r in rows])
@app.get('/api/shop')
def shop():
    u,e=require_user()
    if e:return e
    return jsonify(balance_products=[{'id':'stars_50','title':'50 Stars','stars':50},{'id':'stars_150','title':'150 Stars','stars':150},{'id':'stars_500','title':'500 Stars','stars':500}],store_products=[{'id':'premium_30','type':'premium','title':'Premium 30 дней','description':'👑 Premium на 30 дней','stars':100},{'id':'boost_x2','type':'boost','title':'x2 Coins','description':'⚡ Буст Coins на 24 часа','stars':50},{'id':'boost_xp','type':'boost','title':'x2 XP','description':'⚡ Буст XP на 24 часа','stars':50}])

PRODUCT_PRICES={'stars_50':50,'stars_150':150,'stars_500':500,'premium_30':100,'boost_x2':50,'boost_xp':50}
def payload(tid,kind,product):return f'vldst:{tid}:{kind}:{product}:{secrets.token_hex(8)}'
async def make_invoice(tid,kind,product,amount):
    p=payload(tid,kind,product)
    with db() as con:
        with con.cursor() as cur:cur.execute('INSERT INTO payments(telegram_id,payload,kind,product_id,amount) VALUES(%s,%s,%s,%s,%s)',(tid,p,kind,product,amount))
        con.commit()
    return await bot_instance.create_invoice_link(title='VLDST CASE',description=f'{kind}: {product}',payload=p,currency='XTR',prices=[{'label':product,'amount':amount}])
@app.post('/api/stars/invoice')
def invoice():
    u,e=require_user()
    if e:return e
    d=request.get_json() or {};kind=d.get('kind');product=str(d.get('product') or d.get('case_id') or '')
    if kind=='case':
        try:cid=int(d.get('case_id'))
        except:return jsonify(error='case_not_found'),400
        with db() as con:
            with con.cursor() as cur:cur.execute('SELECT price_stars FROM cases WHERE id=%s AND active',(cid,));r=cur.fetchone()
        if not r:return jsonify(error='case_not_found'),404
        amount=int(r['price_stars'])
    else:
        amount=PRODUCT_PRICES.get(product)
        if not amount:return jsonify(error='product_not_found'),400
    try:
        url=asyncio.run_coroutine_threadsafe(make_invoice(u['telegram_id'],kind,product,amount),BOT_LOOP).result(15);return jsonify(invoice_url=url)
    except Exception as ex:return jsonify(error='invoice_failed',message=str(ex)),500

@app.get('/api/admin/stats')
def astats():
    u,e=require_admin()
    if e:return e
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT COUNT(*) n FROM users');users=cur.fetchone()['n'];cur.execute('SELECT COUNT(*) n FROM users WHERE banned');banned=cur.fetchone()['n'];cur.execute('SELECT COALESCE(SUM(coins),0) n FROM users');coins=cur.fetchone()['n'];cur.execute('SELECT COUNT(*) n FROM inventory WHERE sold_at IS NULL');inv=cur.fetchone()['n']
    return jsonify(users=users,banned=banned,coins=coins,inventory=inv)
@app.get('/api/admin/users')
def ausers():
    u,e=require_admin()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT telegram_id,username,first_name,coins,stars,level,banned FROM users ORDER BY id DESC LIMIT 1000');rows=cur.fetchall()
    return jsonify(users=[dict(r) for r in rows])
@app.get('/api/admin/cases')
def acases():
    u,e=require_admin()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT id,name,price_coins,price_stars,active FROM cases ORDER BY id');rows=cur.fetchall()
    return jsonify(cases=[dict(r) for r in rows])
def admin_update(sql,args):
    u,e=require_admin()
    if e:return e
    with db() as con:
        with con.cursor() as cur:cur.execute(sql,args)
        con.commit()
    return jsonify(ok=True)
@app.post('/api/admin/give-coins')
def givecoins():
    d=request.get_json() or {};return admin_update('UPDATE users SET coins=coins+%s WHERE telegram_id=%s',(int(d.get('amount',10000)),int(d['telegram_id'])))
@app.post('/api/admin/give-stars')
def givestars():
    d=request.get_json() or {};return admin_update('UPDATE users SET stars=stars+%s WHERE telegram_id=%s',(int(d.get('amount',100)),int(d['telegram_id'])))
@app.post('/api/admin/user/<int:tid>/premium')
def prem(tid):return admin_update("UPDATE users SET premium_until=GREATEST(COALESCE(premium_until,NOW()),NOW())+INTERVAL '30 days' WHERE telegram_id=%s",(tid,))
@app.post('/api/admin/user/<int:tid>/ban')
def ban(tid):
    d=request.get_json() or {};return admin_update('UPDATE users SET banned=%s WHERE telegram_id=%s',(bool(d.get('banned')),tid))
@app.post('/api/admin/cases/<int:cid>/toggle')
def toggle(cid):return admin_update('UPDATE cases SET active=NOT active WHERE id=%s',(cid,))

router=Router()
@router.message(CommandStart())
async def start(m:Message):
    ref=None; parts=(m.text or '').split(maxsplit=1)
    if len(parts)>1 and parts[1].startswith('ref_'):
        try:ref=int(parts[1][4:])
        except:ref=None
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE telegram_id=%s',(m.from_user.id,));exists=cur.fetchone()
            if not exists:
                cur.execute('INSERT INTO users(telegram_id,username,first_name,referred_by) VALUES(%s,%s,%s,%s)',(m.from_user.id,m.from_user.username,m.from_user.first_name or 'Игрок',ref if ref!=m.from_user.id else None))
                if ref and ref!=m.from_user.id:cur.execute('UPDATE users SET coins=coins+500 WHERE telegram_id=%s',(ref,))
        con.commit()
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🎁 Открыть VLDST CASE',web_app=WebAppInfo(url=WEBAPP_URL+'/webapp/'))]])
    await m.answer('🔥 <b>VLDST CASE</b>\n\nКейсы • Coins • Stars • Premium • рейтинг',reply_markup=kb)
@router.message(Command('admin'))
async def admin_cmd(m:Message):
    if m.from_user.id not in ADMIN_IDS:return await m.answer('⛔ Доступ запрещён.')
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⚙️ Открыть ADMIN',web_app=WebAppInfo(url=WEBAPP_URL+'/webapp/admin.html'))]])
    await m.answer('🛠 <b>VLDST ADMIN</b>',reply_markup=kb)
@router.pre_checkout_query()
async def pre(q:PreCheckoutQuery):await q.answer(ok=True)
@router.message(lambda m: bool(m.successful_payment))
async def paid(m:Message):
    p=m.successful_payment
    with db() as con:
        with con.cursor() as cur:
            cur.execute('SELECT * FROM payments WHERE payload=%s FOR UPDATE',(p.invoice_payload,));row=cur.fetchone()
            if not row or row['status']=='paid':return
            cur.execute("UPDATE payments SET status='paid' WHERE payload=%s",(p.invoice_payload,))
            if row['kind']=='balance':cur.execute('UPDATE users SET stars=stars+%s WHERE telegram_id=%s',(row['amount'],row['telegram_id']))
            elif row['product_id']=='premium_30':cur.execute("UPDATE users SET premium_until=GREATEST(COALESCE(premium_until,NOW()),NOW())+INTERVAL '30 days' WHERE telegram_id=%s",(row['telegram_id'],))
            elif row['product_id']=='boost_x2':cur.execute("INSERT INTO boosts(user_id,type,expires_at) SELECT id,'x2_coins',NOW()+INTERVAL '24 hours' FROM users WHERE telegram_id=%s",(row['telegram_id'],))
            elif row['product_id']=='boost_xp':cur.execute("INSERT INTO boosts(user_id,type,expires_at) SELECT id,'x2_xp',NOW()+INTERVAL '24 hours' FROM users WHERE telegram_id=%s",(row['telegram_id'],))
            elif row['kind']=='case':
                try: cid=int(row['product_id'])
                except: cid=0
                cur.execute('SELECT * FROM items WHERE case_id=%s',(cid,)); items=cur.fetchall()
                total=sum(float(i['weight']) for i in items)
                if items and total>0:
                    x=secrets.SystemRandom().random()*total; acc=0; chosen=items[-1]
                    for it in items:
                        acc+=float(it['weight'])
                        if x<=acc:
                            chosen=it; break
                    cur.execute('INSERT INTO inventory(user_id,item_id) SELECT id,%s FROM users WHERE telegram_id=%s',(chosen['id'],row['telegram_id']))
                    cur.execute('UPDATE users SET xp=xp+10 WHERE telegram_id=%s',(row['telegram_id'],))
        con.commit()
    await m.answer('⭐ Оплата подтверждена!')

async def broadcast(text):
    sent=failed=0
    with db() as con:
        with con.cursor() as cur:cur.execute('SELECT telegram_id FROM users WHERE banned=FALSE');ids=[r['telegram_id'] for r in cur.fetchall()]
    for tid in ids:
        try:await bot_instance.send_message(tid,text,parse_mode=ParseMode.HTML);sent+=1;await asyncio.sleep(.04)
        except:failed+=1
    return sent,failed
@app.post('/api/admin/broadcast')
def abroadcast():
    u,e=require_admin()
    if e:return e
    text=(request.get_json() or {}).get('text','').strip()
    if not text:return jsonify(error='empty_text'),400
    try:s,f=asyncio.run_coroutine_threadsafe(broadcast(text),BOT_LOOP).result(120);return jsonify(sent=s,failed=f)
    except Exception as ex:return jsonify(error='broadcast_failed',message=str(ex)),500

async def main():
    global BOT_LOOP,bot_instance
    BOT_LOOP=asyncio.get_running_loop();init_db();bot_instance=Bot(BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML));dp=Dispatcher();dp.include_router(router)
    threading.Thread(target=lambda:app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')),debug=False,use_reloader=False),daemon=True).start()
    await bot_instance.delete_webhook(drop_pending_updates=True);await dp.start_polling(bot_instance)
if __name__=='__main__':asyncio.run(main())
