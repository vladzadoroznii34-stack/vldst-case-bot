/* VLDST CASE — upgraded Mini App frontend */
"use strict";

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); tg.enableClosingConfirmation?.(); }

const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[c]));
const attr = esc;
const H = (extra={}) => ({"Content-Type":"application/json","X-Telegram-Init-Data":tg?.initData||"",...extra});
let casesCache=[];
let inventoryCache=[];
let inventoryFilter="all";
let rouletteTimer=null;

function haptic(type="light"){ try{tg?.HapticFeedback?.impactOccurred(type)}catch{} }
function toast(text){const e=$("toast");if(!e)return;e.textContent=text;e.classList.add("show");clearTimeout(window.__toast);window.__toast=setTimeout(()=>e.classList.remove("show"),2500)}

async function api(url, options={}){
  let r;
  try{r=await fetch(url,{...options,headers:H(options.headers||{})})}catch{throw new Error("Сервер недоступен. Проверь Flask.")}
  let d={};try{d=await r.json()}catch{}
  if(!r.ok){
    if(r.status===401||d.error==="unauthorized")throw new Error("Открой VLDST CASE через Telegram");
    if(r.status===403)throw new Error(d.error==="banned"?"Ваш аккаунт заблокирован":"Доступ запрещён");
    const map={not_enough_coins:"Недостаточно Coins",case_not_found:"Кейс не найден",case_has_no_items:"В кейсе нет предметов",already_claimed:"Награда уже получена",task_not_found:"Задание не найдено",user_not_found:"Пользователь не найден",payment_unavailable:"Оплата сейчас недоступна"};
    throw new Error(map[d.error]||d.message||d.error||`Ошибка ${r.status}`)
  }
  return d;
}

function imageSrc(src,type="item",label="VLDST",rarity="common",seed=1){
  if(src&&String(src).trim())return src;
  const A=window.VLDST_ASSETS;
  if(type==="case")return A.case(label,seed);
  if(type==="premium")return A.premium(label);
  if(type==="boost")return A.boost(label);
  if(type==="game")return A.game(label);
  if(type==="task")return A.task(label);
  if(type==="ref")return A.ref(label);
  return A.item(label,rarity,seed);
}
function img(src,cls="",type="item",label="VLDST",rarity="common",seed=1){return `<img class="${cls}" src="${attr(imageSrc(src,type,label,rarity,seed))}" loading="lazy" alt="${attr(label)}" onerror="this.onerror=null;this.src='${window.VLDST_ASSETS.fallback()}'">`}

function openModal(content, options={}){
  const m=$("modal"),s=$("sheet");if(!m||!s)return;
  s.innerHTML=content;m.classList.add("open");s.scrollTop=0;tg?.BackButton?.show();
  if(options.onOpen)options.onOpen();
}
function closeModal(){clearTimeout(rouletteTimer);if(gameState?.active){gameState.active=false;clearInterval(gameState.timer);clearInterval(gameState.move)}$("modal")?.classList.remove("open");tg?.BackButton?.hide()}
$("modal")?.addEventListener("click",e=>{if(e.target.id==="modal")closeModal()});
tg?.BackButton?.onClick(closeModal);
function setNav(btn){document.querySelectorAll(".nav button").forEach(b=>b.classList.remove("active"));btn?.classList.add("active")}
function goHome(btn){window.scrollTo({top:0,behavior:"smooth"});setNav(btn)}
function openCases(btn){$("casesSection")?.scrollIntoView({behavior:"smooth",block:"start"});setNav(btn)}
function checkAuth(){return Boolean(tg?.initData)}

async function loadUser(){
  try{
    const u=await api("/api/user");
    if(u.banned){openModal(`<div class="result">${img(null,"result-img","item","BLOCKED","mythic",999)}<h2>⛔ АККАУНТ ЗАБЛОКИРОВАН</h2><p class="muted">Доступ к VLDST CASE ограничен.</p></div>`);return u}
    $("balance").textContent=`🪙 ${Number(u.coins||0).toLocaleString()}  ⭐ ${Number(u.stars||0).toLocaleString()}`;
    $("name").textContent=u.first_name||"Игрок";
    $("level").textContent=`Уровень ${Number(u.level||1)} • ${Number(u.xp||0).toLocaleString()} XP`;
    const xp=Number(u.xp||0), level=Number(u.level||1), pct=Math.min(100,Math.round((xp%100)));
    $("xpbar").style.width=`${pct}%`; $("xpText").textContent=`${pct}/100 XP`;
    $("premium").textContent=u.premium_until?"👑 PREMIUM":"FREE";
    if($("heroCoins"))$("heroCoins").textContent=Number(u.coins||0).toLocaleString();
    return u;
  }catch(e){console.error(e);toast(e.message)}
}

async function loadCases(){
  try{
    const d=await api("/api/cases");casesCache=Array.isArray(d.cases)?d.cases:[];
    $("caseCount").textContent=`${casesCache.length} кейсов`;
    $("cases").innerHTML=casesCache.map((c,i)=>`<article class="card case-card" style="--delay:${i*45}ms"><button class="case-open" onclick="caseInfo(${Number(c.id)})">${img(c.image_url,"case-img","case",c.name,"common",i+1)}<div class="case-body"><div class="case-title"><b>${esc(c.name)}</b><span class="case-arrow">›</span></div><div class="case-price"><span class="price">🪙 ${Number(c.price_coins||0).toLocaleString()}</span><span class="pill">ОТКРЫТЬ</span></div></div></button></article>`).join("")||`<div class="card empty-card">Кейсов пока нет.</div>`;
    await loadItems(casesCache);
  }catch(e){console.error(e);toast("Не удалось загрузить кейсы")}
}

async function loadItems(cases){
  const all=[];for(const c of cases){try{const d=await api(`/api/cases/${c.id}/items`);if(Array.isArray(d.items))all.push(...d.items)}catch(e){console.warn(e)}}
  const seen=new Set(), unique=all.filter(x=>{const k=x.id??`${x.name}-${x.rarity}`;if(seen.has(k))return false;seen.add(k);return true}).slice(0,49);
  $("itemCount").textContent=`${unique.length} шт.`;
  $("items").innerHTML=unique.map((x,i)=>itemCard(x,i,false)).join("")||`<p class="muted">Предметов пока нет.</p>`;
}
function itemCard(item,index=1,withSell=false){
  const rarity=String(item.rarity||"common").toLowerCase();
  const seed=window.VLDST_ASSETS.hash(`${item.id||""}|${item.name||""}`)||index;
  return `<article class="item ${esc(rarity)}" data-rarity="${esc(rarity)}">${img(item.image_url,"","item",item.name||"ITEM",rarity,seed)}<div class="item-name">${esc(item.name||"Предмет")}</div><div class="item-meta"><span>${esc((item.rarity||"COMMON").toUpperCase())}</span>${item.sell_price!=null?`<b>🪙 ${Number(item.sell_price||0).toLocaleString()}</b>`:""}</div>${withSell?`<button class="sell-btn" onclick="sell(${Number(item.inventory_id)})">ПРОДАТЬ</button>`:""}</article>`;
}

async function caseInfo(id){
  try{
    const c=casesCache.find(x=>Number(x.id)===Number(id))||(await api("/api/cases")).cases?.find(x=>Number(x.id)===Number(id));if(!c)throw new Error("Кейс не найден");
    const d=await api(`/api/cases/${id}/items`),items=d.items||[];
    openModal(`<div class="case-hero-modal">${img(c.image_url,"case-modal-art","case",c.name,"common",Number(id)||1)}<div><span class="premium-tag">VLDST DROP</span><h2>${esc(c.name)}</h2><p class="muted">${esc(c.description||"Открой кейс и получи случайный предмет.")}</p></div></div><div class="price-grid"><button class="primary" onclick="openCase(${Number(id)})">🪙 ${Number(c.price_coins||0).toLocaleString()} <small>OPEN</small></button><button class="primary stars-btn" onclick="buyCase(${Number(id)})">⭐ ${Number(c.price_stars||0)} <small>STARS</small></button></div><div class="drop-title"><h3>🎁 Возможные предметы</h3><span class="muted">${items.length} предметов</span></div><div class="item-grid">${items.map((x,i)=>itemCard(x,i)).join("")||`<p class="muted">Предметов нет.</p>`}</div>`,{onOpen:()=>haptic("light")});
  }catch(e){toast(e.message)}
}

async function openCase(id){
  try{
    closeModal();haptic("medium");toast("🎁 Получаем результат...");
    const result=await api(`/api/cases/${id}/open`,{method:"POST"});if(!result.item)throw new Error("Не удалось получить предмет");
    const c=casesCache.find(x=>Number(x.id)===Number(id));
    const d=await api(`/api/cases/${id}/items`).catch(()=>({items:[]}));
    const pool=d.items||[];await playRoulette(c?.name||"CASE",pool,result.item);
  }catch(e){toast(e.message)}
}

function rouletteCard(item,index){
  const r=String(item.rarity||"common").toLowerCase(),seed=window.VLDST_ASSETS.hash(`${item.id||""}|${item.name||""}`)||index+1;
  return `<div class="roulette-item ${esc(r)}">${img(item.image_url,"roulette-img","item",item.name||"ITEM",r,seed)}<b>${esc(item.name||"Предмет")}</b><span>${esc((item.rarity||"COMMON").toUpperCase())}</span></div>`;
}
async function playRoulette(caseName,pool,winner){
  const source=pool.length?pool:[winner];const items=[];for(let i=0;i<28;i++)items.push(source[Math.floor(Math.random()*source.length)]);const winIndex=22;items[winIndex]=winner;
  openModal(`<div class="roulette-screen"><span class="premium-tag">🎰 DROP MACHINE</span><h2>${esc(caseName)}</h2><p class="muted">Колесо уже запущено…</p><div class="roulette-wrap"><div class="roulette-pointer"></div><div id="rouletteTrack" class="roulette-track">${items.map((x,i)=>rouletteCard(x,i)).join("")}</div></div><div class="roulette-controls"><button id="skipRoulette" class="ghost-btn" onclick="finishRoulette()">ПРОПУСТИТЬ</button></div></div>`);
  const track=$("rouletteTrack");const card=track?.querySelector(".roulette-item");if(!track||!card)return finishRoulette(winner);
  const gap=10, width=card.getBoundingClientRect().width+gap, target=winIndex*width;
  track.style.setProperty("--roulette-x",`${Math.max(0,target-(track.parentElement.clientWidth/2-card.getBoundingClientRect().width/2))}px`);
  track.classList.add("spinning");
  rouletteTimer=setTimeout(()=>finishRoulette(winner),4300);
  window.__rouletteWinner=winner;
}
function finishRoulette(winner=window.__rouletteWinner){clearTimeout(rouletteTimer);window.__rouletteWinner=null;haptic("heavy");const r=String(winner?.rarity||"common").toLowerCase();openModal(`<div class="result win-result"><div class="win-burst">✦</div><span class="premium-tag">ВЫПАЛ ПРЕДМЕТ</span><h2>🎉 ПОЗДРАВЛЯЕМ!</h2>${img(winner?.image_url,"result-img","item",winner?.name||"ITEM",r,window.VLDST_ASSETS.hash(winner?.name)||77)}<h2>${esc(winner?.name||"Предмет")}</h2><div class="rarity-badge rarity-${esc(r)}">${esc((winner?.rarity||"COMMON").toUpperCase())}</div><p class="muted">Цена продажи: 🪙 ${Number(winner?.sell_price||0).toLocaleString()}</p><button class="primary" onclick="closeModal();load()">ЗАБРАТЬ</button></div>`);loadUser()}

function openInvoice(url){if(!url)return toast("Ссылка оплаты не создана");if(tg?.openInvoice)tg.openInvoice(url,status=>{if(status==="paid"){toast("⭐ Оплата успешна!");setTimeout(load,700)}else if(status==="cancelled")toast("Оплата отменена");else if(status==="failed")toast("Оплата не прошла")});else window.open(url,"_blank","noopener")}
async function buyCase(id){try{const d=await api("/api/stars/invoice",{method:"POST",body:JSON.stringify({kind:"case",case_id:id})});openInvoice(d.invoice_url)}catch(e){toast(e.message)}}

function productRow(p,kind,type){return `<div class="card shop-row"><img class="shop-img" src="${attr(imageSrc(null,type,p.title||"VLDST",type==="premium"?"mythic":"epic",window.VLDST_ASSETS.hash(p.id||p.title)))}"><div class="shop-copy"><b>${esc(p.title)}</b><div class="muted">${esc(p.description||"")}</div></div><button class="primary small" onclick="buyProduct('${attr(p.id)}','${attr(kind)}')">⭐ ${Number(p.stars||0)}</button></div>`}
async function showShop(){
  openModal(`<div class="shop-head">${img(null,"shop-hero-art","premium","VLDST PREMIUM")}<div><span class="premium-tag">OFFICIAL STORE</span><h2>⭐ Магазин VLDST</h2><p class="muted">Premium, бусты и пополнение Stars.</p></div></div><div id="shoplist"><div class="loading">Загрузка магазина…</div></div>`);
  try{const d=await api("/api/shop"),bp=d.balance_products||[],sp=d.store_products||[];$("shoplist").innerHTML=`<h3>⭐ Пополнение</h3>${bp.map(p=>productRow(p,"balance","premium")).join("")||`<p class="muted">Нет наборов.</p>`}<h3>👑 Premium</h3>${sp.filter(p=>p.type==="premium").map(p=>productRow(p,"store","premium")).join("")||`<p class="muted">Premium пока нет.</p>`}<h3>⚡ Бусты</h3>${sp.filter(p=>p.type!=="premium").map(p=>productRow(p,"store","boost")).join("")||`<p class="muted">Бустов пока нет.</p>`}`}catch(e){toast(e.message)}
}
async function buyProduct(id,kind){try{const d=await api("/api/stars/invoice",{method:"POST",body:JSON.stringify({kind,product:id})});openInvoice(d.invoice_url)}catch(e){toast(e.message)}}

let gameState=null;
function showMini(){openModal(`<div class="game-screen"><div class="game-top">${img(null,"game-art","game","VLDST RUSH")}<div><span class="premium-tag">10 SEC</span><h2>⚡ VLDST RUSH</h2><p class="muted">Лови светящиеся цели. Чем больше комбо — тем выше счёт.</p></div></div><div class="game-stats"><div><small>СЧЁТ</small><b id="gScore">0</b></div><div><small>КОМБО</small><b id="gCombo">0x</b></div><div><small>ВРЕМЯ</small><b id="gTime">10.0</b></div></div><div id="gameArena" class="game-arena"><div class="game-start"><span>🎯</span><b>Готов?</b><small>Нажимай на цель как можно быстрее</small><button class="primary" onclick="startRush()">НАЧАТЬ</button></div></div></div>`)}
function startRush(){
  if(gameState?.timer)clearInterval(gameState.timer);haptic("medium");const arena=$("gameArena");if(!arena)return;
  gameState={score:0,combo:0,time:10,active:true,timer:null,move:null};arena.innerHTML='<button id="target" class="rush-target" onclick="hitTarget(event)">✦</button><div class="combo-pop" id="comboPop"></div>';
  moveTarget();gameState.move=setInterval(moveTarget,700);gameState.timer=setInterval(()=>{gameState.time-=.1;$("gTime").textContent=Math.max(0,gameState.time).toFixed(1);if(gameState.time<=0)endRush()},100);updateGame();
}
function moveTarget(){if(!gameState?.active)return;const a=$("gameArena"),t=$("target");if(!a||!t)return;const pad=20,maxX=Math.max(0,a.clientWidth-t.offsetWidth-pad*2),maxY=Math.max(0,a.clientHeight-t.offsetHeight-pad*2);t.style.left=`${pad+Math.random()*maxX}px`;t.style.top=`${pad+Math.random()*maxY}px`;t.style.transform=`rotate(${Math.random()*40-20}deg) scale(${.85+Math.random()*.3})`}
function hitTarget(e){e?.stopPropagation();if(!gameState?.active)return;gameState.combo++;gameState.score+=10+Math.min(90,gameState.combo*5);haptic(gameState.combo%5===0?"heavy":"light");const p=$("comboPop");if(p){p.textContent=`+${10+Math.min(90,gameState.combo*5)} ${gameState.combo>=3?`🔥 ${gameState.combo}x`:""}`;p.classList.remove("pop");void p.offsetWidth;p.classList.add("pop")}moveTarget();updateGame()}
function updateGame(){if($("gScore"))$("gScore").textContent=gameState.score;if($("gCombo"))$("gCombo").textContent=`${gameState.combo}x`}
async function endRush(){if(!gameState?.active)return;gameState.active=false;clearInterval(gameState.timer);clearInterval(gameState.move);haptic("heavy");const score=gameState.score;const arena=$("gameArena");if(arena)arena.innerHTML='<div class="loading">Подсчитываем награду…</div>';try{const d=await api("/api/minigame/play",{method:"POST",body:JSON.stringify({score})});openModal(`<div class="result"><div class="win-burst">⚡</div><span class="premium-tag">RUSH COMPLETE</span><h2>ИГРА ОКОНЧЕНА</h2><div class="score-final"><span>Счёт</span><b>${score}</b><small>Лучшее комбо: ${gameState.combo}x</small></div><div class="reward-big">+${Number(d.reward||0).toLocaleString()} 🪙</div><button class="primary" onclick="showMini()">ЕЩЁ РАЗ</button></div>`);await loadUser()}catch(e){toast(e.message)}}

async function showRef(){try{const d=await api("/api/referrals");openModal(`<div class="result">${img(null,"result-img","ref","REFERRALS")}<span class="premium-tag">INVITE & EARN</span><h2>👥 РЕФЕРАЛЫ</h2><div class="profile-stats"><div><b>${Number(d.count||0)}</b><small>Приглашено</small></div><div><b>${Number(d.earned||0).toLocaleString()}</b><small>Coins</small></div></div><p class="muted">За нового игрока — 500 Coins.</p><input id="refLink" value="${attr(d.referral_link||"")}" readonly><button class="primary" onclick="copyReferral()">🔗 КОПИРОВАТЬ</button><button class="primary secondary-btn" onclick="shareReferral()">📤 ПРИГЛАСИТЬ</button></div>`)}catch(e){toast(e.message)}}
async function copyReferral(){const i=$("refLink");if(!i)return;try{await navigator.clipboard.writeText(i.value)}catch{i.select();document.execCommand("copy")}toast("Ссылка скопирована");haptic("light")}
function shareReferral(){const i=$("refLink");if(!i)return;const u=encodeURIComponent(i.value),t=encodeURIComponent("🎁 Заходи в VLDST CASE и получай Coins!");const url=`https://t.me/share/url?url=${u}&text=${t}`;if(tg?.openTelegramLink)tg.openTelegramLink(url);else window.open(url,"_blank","noopener")}

async function showTasks(){try{const d=await api("/api/tasks");openModal(`<div class="sheet-head"><div>${img(null,"modal-icon","task","TASKS")}</div><div><span class="premium-tag">MISSIONS</span><h2>🎯 Задания</h2></div></div>${(d.tasks||[]).map(t=>`<div class="card task-row"><div class="task-icon">✓</div><div class="task-copy"><b>${esc(t.title)}</b><p class="muted">${esc(t.description||"")}</p><span class="price">🪙 ${Number(t.reward_coins||0).toLocaleString()} ${t.reward_stars?`⭐ ${Number(t.reward_stars)}`:""}</span></div><button class="primary small" onclick="claim(${Number(t.id)})" ${t.claimed?"disabled":""}>${t.claimed?"✓":"ЗАБРАТЬ"}</button></div>`).join("")||`<p class="muted">Новых заданий нет.</p>`}`)}catch(e){toast(e.message)}}
async function claim(id){try{await api(`/api/tasks/${id}/claim`,{method:"POST"});toast("🎁 Награда получена!");await loadUser();await showTasks()}catch(e){toast(e.message)}}

async function showInventory(){
  try{const d=await api("/api/inventory");inventoryCache=d.inventory||[];inventoryFilter="all";renderInventory();openModal(`<div class="inventory-head"><div>${img(null,"inventory-art","item","INVENTORY","epic",42)}</div><div><span class="premium-tag">YOUR LOOT</span><h2>🎒 Инвентарь</h2><p class="muted">${inventoryCache.length} предметов • сортировка по редкости</p></div></div><div class="inventory-tools"><input id="invSearch" oninput="renderInventory()" placeholder="🔎 Поиск предмета"><div class="filter-row"><button class="filter active" data-filter="all" onclick="setInventoryFilter('all')">Все</button><button class="filter" data-filter="common" onclick="setInventoryFilter('common')">Common</button><button class="filter" data-filter="rare" onclick="setInventoryFilter('rare')">Rare</button><button class="filter" data-filter="epic" onclick="setInventoryFilter('epic')">Epic</button><button class="filter" data-filter="legendary" onclick="setInventoryFilter('legendary')">Legend</button><button class="filter" data-filter="mythic" onclick="setInventoryFilter('mythic')">Mythic</button></div></div><div id="inventoryGrid" class="item-grid inventory-grid"></div>`);renderInventory()}catch(e){toast(e.message)}}
function setInventoryFilter(f){inventoryFilter=f;document.querySelectorAll(".filter").forEach(b=>b.classList.toggle("active",b.dataset.filter===f));renderInventory()}
function renderInventory(){const box=$("inventoryGrid");if(!box)return;const q=($("invSearch")?.value||"").toLowerCase();const list=inventoryCache.filter(x=>(inventoryFilter==="all"||String(x.rarity||"common").toLowerCase()===inventoryFilter)&&String(x.name||"").toLowerCase().includes(q));box.innerHTML=list.map((x,i)=>itemCard(x,i,true)).join("")||`<div class="empty-card"><b>Пусто</b><p class="muted">Здесь пока нет подходящих предметов.</p></div>`}
async function sell(id){try{const d=await api(`/api/inventory/${id}/sell`,{method:"POST"});toast(`Продано за ${Number(d.sold_for||0).toLocaleString()} Coins`);haptic("light");await loadUser();await showInventory()}catch(e){toast(e.message)}}

async function showProfile(){try{const u=await api("/api/user"),initial=(u.first_name||"V").trim().charAt(0).toUpperCase(),xp=Number(u.xp||0),level=Number(u.level||1),pct=xp%100;openModal(`<div class="profile-modal"><div class="profile-cover"><div class="profile-avatar">${esc(initial)}</div><span class="premium-tag">${u.premium_until?"👑 PREMIUM":"FREE"}</span></div><h2>${esc(u.first_name||"Игрок")}</h2><p class="muted">${u.username?`@${esc(u.username)}`:"@player"} • ID ${esc(u.telegram_id)}</p><div class="level-card"><div class="row"><b>Уровень ${level}</b><span>${xp.toLocaleString()} XP</span></div><div class="progress large"><i style="width:${pct}%"></i></div><div class="level-foot"><span>${pct}/100 XP</span><span>До уровня ${Math.max(0,100-pct)} XP</span></div></div><div class="profile-stats"><div><span>🪙</span><b>${Number(u.coins||0).toLocaleString()}</b><small>Coins</small></div><div><span>⭐</span><b>${Number(u.stars||0).toLocaleString()}</b><small>Stars</small></div><div><span>🎒</span><b>${inventoryCache.length||0}</b><small>Loot</small></div><div><span>🏆</span><b>${level}</b><small>Level</small></div></div><div class="profile-actions"><button class="primary" onclick="showInventory()">🎒 ИНВЕНТАРЬ</button><button class="primary secondary-btn" onclick="showLeaderboard()">🏆 РЕЙТИНГ</button></div><div class="premium-box">${u.premium_until?`👑 Premium активен до ${new Date(u.premium_until).toLocaleDateString()}`:`✨ Подключи Premium в магазине и получай больше возможностей.`}</div></div>`)}catch(e){toast(e.message)}}

async function showLeaderboard(){try{const d=await api("/api/leaderboard");openModal(`<div class="sheet-head"><div class="modal-icon trophy">🏆</div><div><span class="premium-tag">TOP PLAYERS</span><h2>Рейтинг</h2></div></div>${(d.leaderboard||[]).map((u,i)=>`<div class="rank-row ${i<3?"podium":""}"><b class="rank-num">${i===0?"🥇":i===1?"🥈":i===2?"🥉":"#"+(i+1)}</b><span><b>${esc(u.first_name||"Игрок")}</b><small>${u.username?`@${esc(u.username)}`:""}</small></span><strong>LVL ${Number(u.level||1)}</strong><span>${Number(u.xp||0).toLocaleString()} XP</span></div>`).join("")||`<p class="muted">Рейтинг пуст.</p>`}`)}catch(e){toast(e.message)}}

async function showBoosts(){try{const d=await api("/api/boosts");openModal(`<div class="sheet-head"><div>${img(null,"modal-icon-img","boost","BOOSTS")}</div><div><span class="premium-tag">ACTIVE</span><h2>⚡ Мои бусты</h2></div></div>${(d.boosts||[]).map((b,i)=>`<div class="card boost-row">${img(null,"boost-mini","boost",b.type||"BOOST", "epic", i+1)}<div class="shop-copy"><b>${esc(b.type||"BOOST")}</b><div class="muted">До: ${b.expires_at?new Date(b.expires_at).toLocaleString():"—"}</div></div><span class="pill">ACTIVE</span></div>`).join("")||`<p class="muted">Активных бустов нет.</p>`}<button class="primary" onclick="showShop()">⭐ ОТКРЫТЬ МАГАЗИН</button>`)}catch(e){toast(e.message)}}
async function claimDaily(){try{const d=await api("/api/daily",{method:"POST"});toast(`🎁 +${Number(d.reward||0).toLocaleString()} Coins`);haptic("heavy");await loadUser()}catch(e){toast(e.message==="Награда уже получена"?"⏳ Сегодня награда уже получена":e.message)}}

async function load(){if(!checkAuth()){openModal(`<div class="result">${img(null,"result-img","game","TELEGRAM")}<h2>VLDST CASE</h2><p class="muted">Открой приложение через Telegram.</p></div>`);return}await Promise.all([loadUser(),loadCases()])}
load();
