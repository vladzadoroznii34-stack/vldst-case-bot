import express from "express";
import fs from "fs";
import path from "path";
import crypto from "crypto";
import Database from "better-sqlite3";
import { fileURLToPath } from "url";
import { caseSvg, itemSvg, shopSvg, gameSvg } from "./asset-generator.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const db = new Database(path.join(__dirname,"data","vldst.db"));
db.pragma("journal_mode = WAL");
db.exec(fs.readFileSync(path.join(__dirname,"schema.sql"),"utf8"));
app.use(express.json({limit:"1mb"}));
app.use(express.static(path.join(__dirname,"public")));

const DEMO_MODE = process.env.DEMO_MODE !== "false";
const BOT_TOKEN = process.env.BOT_TOKEN || "";
const ADMIN_KEY = process.env.ADMIN_KEY || "CHANGE_ME";

const send = (res,data,status=200)=>res.status(status).json(data);

function getUser(req){
  const tid = String(req.header("x-telegram-id") || "");
  if(!tid && !DEMO_MODE) return null;
  const telegramId = tid || "demo-1";
  let u = db.prepare("SELECT * FROM users WHERE telegram_id=?").get(telegramId);
  if(!u){
    const code = "VLDST"+crypto.randomBytes(4).toString("hex").toUpperCase();
    db.prepare("INSERT INTO users(telegram_id,username,first_name,referral_code) VALUES(?,?,?,?)")
      .run(telegramId,req.header("x-telegram-username")||"demo",req.header("x-telegram-name")||"VLDST Player",code);
    u = db.prepare("SELECT * FROM users WHERE telegram_id=?").get(telegramId);
  }
  return u;
}
function auth(req,res,next){ const u=getUser(req); if(!u)return send(res,{ok:false,error:"Telegram authorization required"},401); req.user=u; next(); }
function coins(uid,n,type,note){
  db.prepare("UPDATE users SET coins=coins+? WHERE id=?").run(n,uid);
  db.prepare("INSERT INTO transactions(user_id,type,amount,currency,note) VALUES(?,?,?,?,?)").run(uid,type,n,"COINS",note||"");
}
function xp(uid,n){
  const u=db.prepare("SELECT xp FROM users WHERE id=?").get(uid);
  const premium=db.prepare("SELECT 1 FROM user_premium WHERE user_id=? AND expires_at>datetime('now')").get(uid);
  const gain=Math.round(Number(n||0)*(premium?1.25:1));
  const next=(u?.xp||0)+gain;
  db.prepare("UPDATE users SET xp=?,level=? WHERE id=?").run(next,Math.floor(next/100)+1,uid);
}
function boostReward(uid,n){
  const b=db.prepare("SELECT COALESCE(MAX(multiplier),1) m FROM user_boosts WHERE user_id=? AND expires_at>datetime('now')").get(uid);
  return Math.round(Number(n||0)*Number(b?.m||1));
}
function weighted(rows){
  const total=rows.reduce((a,b)=>a+Number(b.drop_chance),0);
  let r=Math.random()*total;
  for(const row of rows){ r-=Number(row.drop_chance); if(r<=0)return row; }
  return rows[rows.length-1];
}


function decorateItem(i){
  if(!i) return i;
  return {...i,image:`/assets-code/item/${i.id}.svg`};
}
function decorateCase(c){
  return {...c,image:`/assets-code/case/${c.id}.svg`};
}

app.get("/assets-code/case/:id.svg",(req,res)=>{
  const c=db.prepare("SELECT id,name,theme FROM cases WHERE id=?").get(Number(req.params.id));
  if(!c)return res.status(404).type("text").send("not found");
  res.type("image/svg+xml").send(caseSvg(c));
});
app.get("/assets-code/item/:id.svg",(req,res)=>{
  const i=db.prepare("SELECT id,name,rarity,theme FROM items WHERE id=?").get(Number(req.params.id));
  if(!i)return res.status(404).type("text").send("not found");
  res.type("image/svg+xml").send(itemSvg(i));
});
app.get("/assets-code/shop/:code.svg",(req,res)=>{
  const p=db.prepare("SELECT * FROM star_shop WHERE code=? AND active=1").get(req.params.code);
  if(!p)return res.status(404).type("text").send("not found");
  res.type("image/svg+xml").send(shopSvg(p));
});
app.get("/assets-code/game.svg",(req,res)=>{
  res.type("image/svg+xml").send(gameSvg());
});

app.get("/api/cases",(req,res)=>{
  const list=db.prepare("SELECT * FROM cases WHERE active=1 ORDER BY id DESC").all();
  for(const c of list){
    c.image=`/assets-code/case/${c.id}.svg`;
    c.items=db.prepare(`SELECT i.*,ci.drop_chance FROM case_items ci JOIN items i ON i.id=ci.item_id WHERE ci.case_id=? ORDER BY ci.drop_chance DESC`).all(c.id);
  }
  send(res,{ok:true,cases:list});
});
app.get("/api/items",(req,res)=>{
  const items=db.prepare("SELECT * FROM items ORDER BY id DESC").all().map(decorateItem);
  send(res,{ok:true,items});
});
app.get("/api/me",auth,(req,res)=>{
  const inventory=db.prepare(`SELECT inv.id,inv.obtained_at,i.* FROM inventory inv JOIN items i ON i.id=inv.item_id WHERE inv.user_id=? AND inv.sold_at IS NULL ORDER BY inv.id DESC`).all(req.user.id).map(decorateItem);
  const referrals=db.prepare("SELECT COUNT(*) c FROM users WHERE referred_by=?").get(req.user.referral_code)?.c||0;
  const boosts=db.prepare("SELECT code,multiplier,expires_at FROM user_boosts WHERE user_id=? AND expires_at>datetime('now') ORDER BY multiplier DESC").all(req.user.id);
  const premium=db.prepare("SELECT product_code,expires_at FROM user_premium WHERE user_id=? AND expires_at>datetime('now')").get(req.user.id)||null;
  const cosmetics=db.prepare("SELECT code,obtained_at FROM user_cosmetics WHERE user_id=? ORDER BY id DESC").all(req.user.id);
  send(res,{ok:true,user:req.user,inventory,referrals,boosts,premium,cosmetics});
});
app.post("/api/daily",auth,(req,res)=>{
  const today=new Date().toISOString().slice(0,10);
  if(req.user.last_daily===today)return send(res,{ok:false,error:"Сегодня награда уже получена"});
  db.prepare("UPDATE users SET last_daily=? WHERE id=?").run(today,req.user.id);
  coins(req.user.id,boostReward(req.user.id,500),"daily","Daily reward"); xp(req.user.id,25);
  send(res,{ok:true,reward:500});
});
app.post("/api/cases/:id/open",auth,(req,res)=>{
  const c=db.prepare("SELECT * FROM cases WHERE id=? AND active=1").get(req.params.id);
  if(!c)return send(res,{ok:false,error:"Кейс не найден"},404);
  if(req.user.coins<c.price_coins)return send(res,{ok:false,error:"Недостаточно Coins"},400);
  const rows=db.prepare(`SELECT ci.*,i.name,i.rarity,i.sell_coins,i.image FROM case_items ci JOIN items i ON i.id=ci.item_id WHERE ci.case_id=?`).all(c.id);
  const win=weighted(rows);
  db.transaction(()=>{
    db.prepare("UPDATE users SET coins=coins-? WHERE id=?").run(c.price_coins,req.user.id);
    db.prepare("INSERT INTO transactions(user_id,type,amount,currency,note) VALUES(?,?,?,?,?)").run(req.user.id,"case_open",-c.price_coins,"COINS",`Case #${c.id}`);
    db.prepare("INSERT INTO inventory(user_id,item_id,obtained_case_id) VALUES(?,?,?)").run(req.user.id,win.item_id,c.id);
    xp(req.user.id,Math.max(10,Math.floor(c.price_coins/1000)));
  })();
  send(res,{ok:true,item:win,case:c});
});
app.post("/api/inventory/:id/sell",auth,(req,res)=>{
  const row=db.prepare(`SELECT inv.*,i.sell_coins,i.name FROM inventory inv JOIN items i ON i.id=inv.item_id WHERE inv.id=? AND inv.user_id=? AND inv.sold_at IS NULL`).get(req.params.id,req.user.id);
  if(!row)return send(res,{ok:false,error:"Предмет не найден"},404);
  db.transaction(()=>{
    db.prepare("UPDATE inventory SET sold_at=CURRENT_TIMESTAMP WHERE id=?").run(row.id);
    coins(req.user.id,row.sell_coins,"item_sell",row.name); xp(req.user.id,5);
  })();
  send(res,{ok:true,coins:row.sell_coins});
});
app.get("/api/tasks",auth,(req,res)=>{
  const tasks=db.prepare("SELECT * FROM tasks WHERE active=1 ORDER BY id").all();
  send(res,{ok:true,tasks:tasks.map(t=>{
    const u=db.prepare("SELECT * FROM user_tasks WHERE user_id=? AND task_id=?").get(req.user.id,t.id);
    return {...t,progress:u?.progress||0,claimed:!!u?.claimed};
  })});
});
app.post("/api/tasks/:id/claim",auth,(req,res)=>{
  const t=db.prepare("SELECT * FROM tasks WHERE id=? AND active=1").get(req.params.id);
  if(!t)return send(res,{ok:false,error:"Задание не найдено"},404);
  const u=db.prepare("SELECT * FROM user_tasks WHERE user_id=? AND task_id=?").get(req.user.id,t.id);
  if(u?.claimed)return send(res,{ok:false,error:"Уже получено"});
  const required=t.kind==="collection"?5:1;
  if((u?.progress||0)<required)return send(res,{ok:false,error:"Задание ещё не выполнено"});
  db.prepare("INSERT OR REPLACE INTO user_tasks(user_id,task_id,progress,claimed) VALUES(?,?,?,1)").run(req.user.id,t.id,u?.progress||required);
  coins(req.user.id,boostReward(req.user.id,t.reward_coins),"task",t.title); xp(req.user.id,t.reward_xp);
  send(res,{ok:true,reward:t.reward_coins});
});
app.get("/api/leaderboard",(req,res)=>send(res,{ok:true,users:db.prepare("SELECT first_name,username,coins,level FROM users ORDER BY coins DESC LIMIT 20").all()}));
app.get("/api/referral",auth,(req,res)=>{
  const count=db.prepare("SELECT COUNT(*) c FROM users WHERE referred_by=?").get(req.user.referral_code)?.c||0;
  send(res,{ok:true,code:req.user.referral_code,count,link:`https://t.me/${process.env.BOT_USERNAME||"VLDSTCaseBot"}?start=ref_${req.user.referral_code}`});
});
app.post("/api/promo",auth,(req,res)=>{
  const code=String(req.body.code||"").trim().toUpperCase();
  const p=db.prepare("SELECT * FROM promo_codes WHERE code=? AND active=1").get(code);
  if(!p||p.uses>=p.max_uses)return send(res,{ok:false,error:"Промокод недействителен"});
  try{
    db.prepare("INSERT INTO promo_uses(code,user_id) VALUES(?,?)").run(code,req.user.id);
    db.prepare("UPDATE promo_codes SET uses=uses+1 WHERE code=?").run(code);
    coins(req.user.id,p.reward_coins,"promo",code);
    send(res,{ok:true,reward:p.reward_coins});
  }catch{send(res,{ok:false,error:"Промокод уже использован"});}
});

// Telegram Stars are implemented only for fixed digital products.
// Randomized case openings remain Coins-only.
app.post("/api/stars/invoice",auth,async(req,res)=>{
  if(!BOT_TOKEN)return send(res,{ok:false,error:"BOT_TOKEN не настроен"},500);
  const catalog={
    premium:{stars:50,title:"VLDST Premium",desc:"Фиксированный Premium Pass"},
    frame:{stars:15,title:"VLDST Frame",desc:"Фиксированная рамка профиля"}
  };
  const product=String(req.body.product||"premium");
  if(!catalog[product])return send(res,{ok:false,error:"Товар не найден"},400);
  const p=catalog[product];
  const body={title:p.title,description:p.desc,payload:`vldst:${product}:${req.user.id}`,currency:"XTR",prices:[{label:p.title,amount:p.stars}]};
  const r=await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/createInvoiceLink`,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});
  const data=await r.json();
  if(!data.ok)return send(res,{ok:false,error:data.description||"Telegram error"},500);
  send(res,{ok:true,url:data.result});
});


// STAR SHOP: fixed, non-random digital products.
app.get("/api/shop",auth,(req,res)=>{
  const products=db.prepare("SELECT * FROM star_shop WHERE active=1 ORDER BY sort_order,id").all();
  const owned=db.prepare("SELECT * FROM user_boosts WHERE user_id=? AND expires_at>datetime('now')").all(req.user.id);
  const premium=db.prepare("SELECT * FROM user_premium WHERE user_id=? AND expires_at>datetime('now') ORDER BY expires_at DESC LIMIT 1").get(req.user.id);
  send(res,{ok:true,products:products.map(p=>({...p,image:`/assets-code/shop/${p.code}.svg`})),owned,premium:premium||null});
});

app.post("/api/shop/invoice",auth,async(req,res)=>{
  if(!BOT_TOKEN)return send(res,{ok:false,error:"BOT_TOKEN не настроен"},500);
  const p=db.prepare("SELECT * FROM star_shop WHERE code=? AND active=1").get(String(req.body.code||""));
  if(!p)return send(res,{ok:false,error:"Товар не найден"},404);
  const payload=`vldst_shop:${p.code}:${req.user.id}:${crypto.randomBytes(5).toString("hex")}`;
  const body={title:p.title,description:p.description,payload,currency:"XTR",prices:[{label:p.title,amount:p.stars}]};
  const r=await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/createInvoiceLink`,{
    method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)
  });
  const data=await r.json();
  if(!data.ok)return send(res,{ok:false,error:data.description||"Telegram error"},500);
  db.prepare("INSERT INTO pending_purchases(user_id,payload,product_code,stars,status) VALUES(?,?,?,?,?)")
    .run(req.user.id,payload,p.code,p.stars,"pending");
  send(res,{ok:true,url:data.result});
});

app.post("/api/game/score",auth,(req,res)=>{
  const score=Math.max(0,Math.min(100,Number(req.body.score)||0));
  const now=Date.now();
  const last=db.prepare("SELECT created_at FROM game_scores WHERE user_id=? ORDER BY id DESC LIMIT 1").get(req.user.id);
  if(last && now-Date.parse(last.created_at)<15000) return send(res,{ok:false,error:"Подожди немного перед новой игрой"},429);
  const reward=boostReward(req.user.id,Math.floor(score*12)+50);
  coins(req.user.id,reward,"mini_game",`Reactor score ${score}`);
  xp(req.user.id,Math.max(5,Math.floor(score/5)));
  db.prepare("INSERT INTO game_scores(user_id,score,reward) VALUES(?,?,?)").run(req.user.id,score,reward);
  send(res,{ok:true,score,reward});
});

app.get("/api/game/top",(req,res)=>{
  send(res,{ok:true,users:db.prepare("SELECT u.first_name,u.username,MAX(g.score) score FROM game_scores g JOIN users u ON u.id=g.user_id GROUP BY g.user_id ORDER BY score DESC LIMIT 20").all()});
});

// Telegram webhook: configure Telegram to POST updates here.
// Stars purchases are granted only after successful_payment.
app.post("/telegram/webhook",(req,res)=>{
  try{
    const upd=req.body||{};
    if(upd.pre_checkout_query){
      fetch(`https://api.telegram.org/bot${BOT_TOKEN}/answerPreCheckoutQuery`,{
        method:"POST",headers:{"content-type":"application/json"},
        body:JSON.stringify({pre_checkout_query_id:upd.pre_checkout_query.id,ok:true})
      }).catch(()=>{});
    }
    const pay=upd.message?.successful_payment;
    if(pay){
      const payload=pay.invoice_payload||"";
      const p=db.prepare("SELECT * FROM pending_purchases WHERE payload=? AND status='pending'").get(payload);
      if(p){
        const u=db.prepare("SELECT * FROM users WHERE id=?").get(p.user_id);
        const product=db.prepare("SELECT * FROM star_shop WHERE code=?").get(p.product_code);
        if(u&&product){
          db.transaction(()=>{
            if(product.kind==="premium"){
              const days=product.duration_days||30;
              db.prepare(`INSERT INTO user_premium(user_id,product_code,expires_at)
                VALUES(?,?,datetime('now', '+'||?||' days'))
                ON CONFLICT(user_id) DO UPDATE SET product_code=excluded.product_code,expires_at=excluded.expires_at`)
                .run(u.id,product.code,days);
            }else if(product.kind==="boost"){
              const days=product.duration_days||7;
              db.prepare(`INSERT INTO user_boosts(user_id,code,multiplier,expires_at)
                VALUES(?,?,?,datetime('now', '+'||?||' days'))`)
                .run(u.id,product.code,product.multiplier||1,days);
            }else{
              db.prepare("INSERT OR IGNORE INTO user_cosmetics(user_id,code) VALUES(?,?)").run(u.id,product.code);
            }
            db.prepare("INSERT INTO purchases(user_id,telegram_payment_charge_id,product_code,stars,status) VALUES(?,?,?,?,?)")
              .run(u.id,pay.telegram_payment_charge_id,p.code,p.stars,"paid");
            db.prepare("UPDATE pending_purchases SET status='paid' WHERE payload=?").run(payload);
          })();
        }
      }
    }
  }catch(e){ console.error("webhook",e); }
  res.json({ok:true});
});

function admin(req,res,next){if(req.header("x-admin-key")!==ADMIN_KEY)return send(res,{ok:false,error:"Forbidden"},403);next();}
app.get("/api/admin/stats",admin,(req,res)=>send(res,{ok:true,stats:{
  users:db.prepare("SELECT COUNT(*) c FROM users").get().c,
  coins:db.prepare("SELECT COALESCE(SUM(coins),0) c FROM users").get().c,
  opens:db.prepare("SELECT COUNT(*) c FROM transactions WHERE type='case_open'").get().c,
  sold:db.prepare("SELECT COUNT(*) c FROM transactions WHERE type='item_sell'").get().c
}}));
app.get("/api/admin/users",admin,(req,res)=>send(res,{ok:true,users:db.prepare("SELECT id,telegram_id,username,first_name,coins,xp,level,created_at FROM users ORDER BY id DESC LIMIT 300").all()}));
app.post("/api/admin/give-coins",admin,(req,res)=>{
  const u=db.prepare("SELECT * FROM users WHERE id=?").get(Number(req.body.userId));
  if(!u)return send(res,{ok:false,error:"User not found"},404);
  coins(u.id,Number(req.body.amount)||0,"admin","Admin adjustment");
  db.prepare("INSERT INTO audit_log(admin,action,payload) VALUES(?,?,?)").run("admin","give_coins",JSON.stringify(req.body));
  send(res,{ok:true});
});
app.post("/api/admin/promo",admin,(req,res)=>{
  const code=String(req.body.code||"").trim().toUpperCase();
  db.prepare("INSERT OR REPLACE INTO promo_codes(code,reward_coins,max_uses,active) VALUES(?,?,?,1)").run(code,Number(req.body.reward)||0,Number(req.body.maxUses)||1);
  send(res,{ok:true});
});

app.get("/api/admin/shop",admin,(req,res)=>send(res,{ok:true,products:db.prepare("SELECT * FROM star_shop ORDER BY sort_order,id").all()}));
app.post("/api/admin/shop/toggle",admin,(req,res)=>{
  const code=String(req.body.code||"");
  db.prepare("UPDATE star_shop SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE code=?").run(code);
  send(res,{ok:true});
});
app.post("/api/admin/shop/price",admin,(req,res)=>{
  const code=String(req.body.code||"");
  const stars=Math.max(1,Number(req.body.stars)||1);
  db.prepare("UPDATE star_shop SET stars=? WHERE code=?").run(stars,code);
  send(res,{ok:true});
});
app.get("/health",(req,res)=>res.json({ok:true,service:"VLDST CASE"}));
app.listen(process.env.PORT||3000,()=>console.log("VLDST CASE running"));
