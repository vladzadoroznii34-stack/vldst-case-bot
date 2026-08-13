// VLDST CASE — full enhanced frontend
// Все базовые картинки генерируются как SVG data-uri: отдельные файлы изображений не обязательны.

const tg=window.Telegram?.WebApp;
if(tg){tg.ready();tg.expand();tg.enableClosingConfirmation?.();}
const $=id=>document.getElementById(id);
const H=()=>({'Content-Type':'application/json','X-Telegram-Init-Data':tg?.initData||''});
let users=[];
let currentCases=[];
let inventoryCache=[];
let miniTimer=null;

function esc(v){return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;");}
function svgData(s){return 'data:image/svg+xml;charset=UTF-8,'+encodeURIComponent(s);}
function asset(kind='case',name='VLDST',rarity='common',seed=0){
 const palettes={common:['#2b3547','#71859e'],rare:['#252b66','#5c70ff'],epic:['#3b1760','#b24dff'],legendary:['#5b2c12','#ff9138'],mythic:['#594b09','#ffe05b']};
 const p=palettes[String(rarity).toLowerCase()]||palettes.common;
 const title=esc(String(name).slice(0,18));
 const icon=kind==='case'?'✦':kind==='boost'?'⚡':kind==='premium'?'♛':kind==='coin'?'🪙':'◆';
 return svgData(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600"><defs><radialGradient id="g"><stop stop-color="${p[1]}" stop-opacity=".8"/><stop offset="1" stop-color="${p[0]}"/></radialGradient><filter id="b"><feGaussianBlur stdDeviation="28"/></filter></defs><rect width="600" height="600" rx="70" fill="#080811"/><circle cx="${100+(seed*73)%400}" cy="130" r="150" fill="${p[1]}" opacity=".24" filter="url(#b)"/><circle cx="300" cy="290" r="185" fill="url(#g)" stroke="${p[1]}" stroke-width="4"/><circle cx="300" cy="290" r="135" fill="#080811" opacity=".7"/><text x="300" y="325" text-anchor="middle" font-size="130">${icon}</text><text x="300" y="500" text-anchor="middle" fill="#fff" font-family="Arial" font-size="38" font-weight="900">${title}</text><text x="300" y="545" text-anchor="middle" fill="${p[1]}" font-family="Arial" font-size="18" font-weight="700">VLDST CASE</text></svg>`);
}
const FALLBACK=asset('case','VLDST','epic',7);
function image(url,kind,name,rarity,seed=0){return url&&String(url).trim()?url:asset(kind,name,rarity,seed);}
function toast(s){const e=$('toast');if(!e)return;e.textContent=s;e.classList.add('show');clearTimeout(window.__toast);window.__toast=setTimeout(()=>e.classList.remove('show'),2400);}
async function api(url,opt={}){const r=await fetch(url,{...opt,headers:{...H(),...(opt.headers||{})}});let d={};try{d=await r.json()}catch{}if(!r.ok){const m={unauthorized:'Открой VLDST CASE через Telegram',banned:'Ваш аккаунт заблокирован',not_enough_coins:'Недостаточно Coins',already_claimed:'Награда уже получена',case_not_found:'Кейс не найден',case_has_no_items:'В кейсе нет предметов',user_not_found:'Пользователь не найден'};throw Error(m[d.error]||d.message||d.error||`Ошибка ${r.status}`)}return d;}
async function post(url,body={}){return api(url,{method:'POST',body:JSON.stringify(body)})}
function openModal(html){const m=$('modal'),s=$('sheet');if(!m||!s)return;s.innerHTML=html;m.classList.add('open');tg?.BackButton?.show();}
function closeModal(){$('modal')?.classList.remove('open');tg?.BackButton?.hide();}
$('modal')?.addEventListener('click',e=>{if(e.target.id==='modal')closeModal()});
tg?.BackButton?.onClick(()=>closeModal());

async function loadUser(){
 try{const u=await api('/api/user');if(!u)return u;
  if(u.banned){openModal(`<div class="result"><div class="game-icon">⛔</div><h2>АККАУНТ ЗАБЛОКИРОВАН</h2><p class="muted">Доступ к VLDST CASE ограничен.</p></div>`);return u}
  if($('balance'))$('balance').textContent=`🪙 ${Number(u.coins||0).toLocaleString()} ⭐ ${Number(u.stars||0).toLocaleString()}`;
  if($('name'))$('name').textContent=u.first_name||'Игрок';
  if($('level'))$('level').textContent=`Уровень ${u.level||1} • ${Number(u.xp||0).toLocaleString()} XP`;
  if($('xpbar'))$('xpbar').style.width=`${Math.min(100,Number(u.xp||0)%100)}%`;
  if($('premium'))$('premium').textContent=u.premium_until?'👑 PREMIUM':'FREE';
  return u;
 }catch(e){console.error(e);toast(e.message)}
}
async function loadCases(){
 try{const d=await api('/api/cases');currentCases=d.cases||[];if($('caseCount'))$('caseCount').textContent=`${currentCases.length} кейсов`;
  $('cases').innerHTML=currentCases.map((c,i)=>`<div class="card case-card"><button class="case-open" onclick="caseInfo(${Number(c.id)})">${`<img class="case-img" src="${esc(image(c.image_url,'case',c.name,'epic',i))}" onerror="this.onerror=null;this.src='${FALLBACK}'">`}<div class="case-body"><b>${esc(c.name)}</b><div class="case-price"><span class="price">🪙 ${Number(c.price_coins||0).toLocaleString()}</span><span class="pill">ОТКРЫТЬ</span></div></div></button></div>`).join('')||'<p class="muted">Кейсов пока нет.</p>';
  await loadItems(currentCases);
 }catch(e){console.error(e);toast('Не удалось загрузить кейсы')}
}
async function loadItems(cases){
 const all=[];for(const c of cases){try{const d=await api(`/api/cases/${c.id}/items`);if(Array.isArray(d.items))all.push(...d.items)}catch{}}
 const seen=new Set();const unique=all.filter(x=>{if(seen.has(x.id))return false;seen.add(x.id);return true});
 $('items').innerHTML=unique.slice(0,60).map((x,i)=>itemCard(x,i)).join('')||'<p class="muted">Предметы появятся здесь.</p>';
}
function itemCard(x,i=0){const r=String(x.rarity||'common').toLowerCase();return `<div class="item ${esc(r)}"><img src="${esc(image(x.image_url,'item',x.name,r,i))}" onerror="this.onerror=null;this.src='${FALLBACK}'"><span>${esc(x.name)}</span></div>`}
async function caseInfo(id){
 try{const c=currentCases.find(x=>Number(x.id)===Number(id))||((await api('/api/cases')).cases||[]).find(x=>Number(x.id)===Number(id));if(!c)return toast('Кейс не найден');const d=await api(`/api/cases/${id}/items`);const items=d.items||[];
  openModal(`<div class="case-modal-head"><img class="modal-case-img" src="${esc(image(c.image_url,'case',c.name,'epic',id))}"><div><h2>${esc(c.name)}</h2><p class="muted">${esc(c.description||'Эксклюзивный кейс VLDST CASE')}</p></div></div><div class="grid"><button class="primary" onclick="openCase(${id})">🪙 ${Number(c.price_coins||0).toLocaleString()}</button><button class="primary stars-btn" onclick="buyCase(${id})">⭐ ${Number(c.price_stars||0)}</button></div><h3>🎁 Содержимое</h3><div class="item-grid">${items.map((x,i)=>itemCard(x,i)).join('')||'<p class="muted">Нет предметов.</p>'}</div>`);
 }catch(e){toast(e.message)}
}
function rollHtml(items,win){
 const pool=items.length?items:currentCases.flatMap(c=>[]);
 const arr=[];for(let i=0;i<34;i++)arr.push(pool[i%Math.max(1,pool.length)]);
 const target=Math.min(27,arr.length-1);if(win&&pool.length)arr[target]=win;
 return arr.map((x,i)=>`<div class="roll-item"><img src="${esc(image(x?.image_url,'item',x?.name||'VLDST',x?.rarity||'common',i))}"><b>${esc(x?.name||'Предмет')}</b></div>`).join('');
}
async function openCase(id){
 try{closeModal();toast('🎰 Запускаем открытие...');const d=await post(`/api/cases/${id}/open`,{});if(!d.item)return toast('Не удалось получить предмет');
  let items=[];try{items=(await api(`/api/cases/${id}/items`)).items||[]}catch{}
  openModal(`<h2>🎰 Открытие кейса</h2><div class="case-roll"><div class="roll-track" id="rollTrack">${rollHtml(items,d.item)}</div></div><p class="muted" style="text-align:center">Определяем награду...</p>`);
  const track=$('rollTrack');requestAnimationFrame(()=>{const card=113;const target=27;const center=260;const x=-(target*card-center+Math.random()*35);track.style.transition='transform 3.8s cubic-bezier(.08,.72,.12,1)';track.style.transform=`translateX(${x}px)`});
  setTimeout(()=>showWin(d.item),4000);
 }catch(e){toast(e.message)}
}
function showWin(item){
 const r=String(item.rarity||'common').toLowerCase();openModal(`<div class="result"><div class="win-ring">🎉</div><h2>ВЫИГРЫШ!</h2><img class="result-img" src="${esc(image(item.image_url,'item',item.name,r,99))}"><h2>${esc(item.name)}</h2><p class="rarity-${esc(r)}">${esc(item.rarity||'COMMON')}</p><p class="muted">Продажа: 🪙 ${Number(item.sell_price||0).toLocaleString()}</p><div class="grid"><button class="primary" onclick="closeModal();load()">ЗАБРАТЬ</button><button class="primary" onclick="openCase(${item.case_id||0})">🎁 ЕЩЁ</button></div></div>`);loadUser();}
async function buyCase(id){try{const d=await post('/api/stars/invoice',{kind:'case',case_id:id});if(!d.invoice_url)return toast('Не удалось создать оплату');openInvoice(d.invoice_url)}catch(e){toast(e.message)}}
function openInvoice(url){if(tg?.openInvoice)tg.openInvoice(url,status=>{if(status==='paid'){toast('⭐ Оплата успешна!');setTimeout(load,700)}});else window.open(url,'_blank')}
async function showShop(){openModal('<h2>⭐ Магазин VLDST</h2><p class="muted">Premium, бусты и пополнение Stars.</p><div id="shoplist">Загрузка...</div>');try{const d=await api('/api/shop');const b=d.balance_products||[],s=d.store_products||[];$('shoplist').innerHTML=`<h3>⭐ Баланс</h3>${b.map(p=>shopRow(p,'balance')).join('')}<h3>👑 Premium</h3>${s.filter(p=>p.type==='premium').map(p=>shopRow(p,'store')).join('')||'<p class="muted">Premium пока не настроен.</p>'}<h3>⚡ Бусты</h3>${s.filter(p=>p.type!=='premium').map(p=>shopRow(p,'store')).join('')||'<p class="muted">Бустов пока нет.</p>'}`}catch(e){toast(e.message)}}
function shopRow(p,k){return `<div class="card shop-row"><div><b>${esc(p.type==='premium'?'👑 ':'⚡ ')}${esc(p.title)}</b><div class="muted">${esc(p.description||'')}</div></div><button class="primary small" onclick="buyProduct('${esc(p.id)}','${k}')">⭐ ${Number(p.stars||0)}</button></div>`}
async function buyProduct(id,kind){try{const d=await post('/api/stars/invoice',{kind,product:id});if(!d.invoice_url)return toast('Ссылка оплаты не создана');openInvoice(d.invoice_url)}catch(e){toast(e.message)}}

async function showInventory(){
 try{const d=await api('/api/inventory');inventoryCache=d.inventory||[];renderInventory('all');}catch(e){toast(e.message)}
}
function renderInventory(filter){
 const list=filter==='all'?inventoryCache:inventoryCache.filter(x=>String(x.rarity||'common').toLowerCase()===filter);
 const filters=['all','common','rare','epic','legendary','mythic'];openModal(`<h2>🎒 Инвентарь</h2><div class="inventory-toolbar"><span class="muted">Предметов: ${inventoryCache.length}</span></div><div class="filter-row">${filters.map(f=>`<button class="filter ${filter===f?'active':''}" onclick="renderInventory('${f}')">${f==='all'?'Все':f.toUpperCase()}</button>`).join('')}</div><div class="item-grid">${list.map((x,i)=>`<div class="item ${esc(String(x.rarity||'common').toLowerCase())}" onclick="inventoryItem(${Number(x.inventory_id)})"><img src="${esc(image(x.image_url,'item',x.name,x.rarity,i))}"><span>${esc(x.name)}</span></div>`).join('')||'<p class="muted">Здесь пока пусто.</p>'}</div>`)}
function inventoryItem(id){const x=inventoryCache.find(i=>Number(i.inventory_id)===Number(id));if(!x)return;openModal(`<div class="result"><img class="result-img" src="${esc(image(x.image_url,'item',x.name,x.rarity,id))}"><h2>${esc(x.name)}</h2><p class="rarity-${esc(String(x.rarity||'common').toLowerCase())}">${esc(x.rarity||'COMMON')}</p><p class="muted">Цена продажи: 🪙 ${Number(x.sell_price||0).toLocaleString()}</p><button class="primary" onclick="sell(${id})">🪙 ПРОДАТЬ</button></div>`)}
async function sell(id){try{const d=await post(`/api/inventory/${id}/sell`,{});toast(`Продано за ${Number(d.sold_for||0).toLocaleString()} Coins`);await loadUser();await showInventory()}catch(e){toast(e.message)}}

async function showProfile(){
 try{const u=await api('/api/user');openModal(`<div class="profile-modal"><div class="avatar big">V</div><h2>${esc(u.first_name||'Игрок')}</h2><p class="muted">${u.username?'@'+esc(u.username):'@player'} • ID ${esc(u.telegram_id)}</p><div class="profile-stats"><div>🪙<b>${Number(u.coins||0).toLocaleString()}</b><small>Coins</small></div><div>⭐<b>${Number(u.stars||0).toLocaleString()}</b><small>Stars</small></div><div>🏆<b>${u.level||1}</b><small>Level</small></div><div>⚡<b>${Number(u.xp||0).toLocaleString()}</b><small>XP</small></div></div><div class="premium-box">${u.premium_until?'👑 Premium активно':'FREE аккаунт'}</div><div class="grid"><button class="primary" onclick="showInventory()">🎒 Инвентарь</button><button class="primary" onclick="showLeaderboard()">🏆 Рейтинг</button></div><h3>📜 Последние выигрыши</h3><div id="history"><p class="muted">История доступна после получения предметов.</p></div></div>`)}catch(e){toast(e.message)}}

async function showLeaderboard(){try{const d=await api('/api/leaderboard');openModal(`<h2>🏆 Рейтинг</h2>${(d.leaderboard||[]).map((u,i)=>`<div class="rank-row"><b>#${i+1}</b><span>${esc(u.first_name||'Игрок')} ${u.username?'@'+esc(u.username):''}</span><strong>LVL ${u.level||1}</strong><span>${Number(u.xp||0).toLocaleString()} XP</span></div>`).join('')||'<p class="muted">Рейтинг пока пуст.</p>'} `)}catch(e){toast(e.message)}}
async function showRef(){try{const d=await api('/api/referrals');openModal(`<div class="result"><div class="game-icon">👥</div><h2>РЕФЕРАЛЫ</h2><p>Приглашено: <b>${Number(d.count||0)}</b></p><p>Заработано: <b>${Number(d.earned||0).toLocaleString()} 🪙</b></p><p class="muted">За нового игрока — 500 Coins.</p><input id="refLink" value="${esc(d.referral_link||'')}" readonly><button class="primary" onclick="copyReferral()">🔗 КОПИРОВАТЬ</button><button class="primary" style="margin-top:8px" onclick="shareReferral()">📤 ПРИГЛАСИТЬ</button></div>`)}catch(e){toast(e.message)}}
async function copyReferral(){const x=$('refLink');if(!x)return;try{await navigator.clipboard.writeText(x.value)}catch{x.select();document.execCommand('copy')}toast('Ссылка скопирована')}
function shareReferral(){const x=$('refLink');if(!x)return;const u=encodeURIComponent(x.value),t=encodeURIComponent('🎁 Заходи в VLDST CASE и получай Coins!');const link=`https://t.me/share/url?url=${u}&text=${t}`;tg?.openTelegramLink?tg.openTelegramLink(link):window.open(link,'_blank')}

async function showTasks(){try{const d=await api('/api/tasks');openModal(`<h2>🎯 Задания</h2>${(d.tasks||[]).map(t=>`<div class="card task-row"><div><b>${esc(t.title)}</b><p class="muted">${esc(t.description||'')}</p><span class="price">🪙 ${Number(t.reward_coins||0).toLocaleString()} ${t.reward_stars?`⭐ ${t.reward_stars}`:''}</span></div><button class="primary small" ${t.claimed?'disabled':''} onclick="claim(${t.id})">${t.claimed?'✓':'ЗАБРАТЬ'}</button></div>`).join('')||'<p class="muted">Новых заданий нет.</p>')}catch(e){toast(e.message)}}
async function claim(id){try{await post(`/api/tasks/${id}/claim`,{});toast('🎁 Награда получена!');await loadUser();showTasks()}catch(e){toast(e.message)}}
async function showBoosts(){try{const d=await api('/api/boosts');openModal(`<h2>⚡ Мои бусты</h2>${(d.boosts||[]).map((b,i)=>`<div class="card shop-row"><div><b>⚡ ${esc(b.type||'BOOST')}</b><div class="muted">До: ${b.expires_at?new Date(b.expires_at).toLocaleString():'—'}</div></div><img style="width:55px;height:55px;border-radius:12px" src="${esc(asset('boost',b.type||'BOOST','epic',i))}"></div>`).join('')||'<p class="muted">Активных бустов нет.</p>'}<button class="primary" onclick="showShop()">⭐ ОТКРЫТЬ МАГАЗИН</button>`)}catch(e){toast(e.message)}}
async function claimDaily(){try{const d=await post('/api/daily',{});toast(`🎁 +${Number(d.reward||0).toLocaleString()} Coins`);loadUser()}catch(e){toast(e.message==='Награда уже получена'?'⏳ Сегодня награда уже получена':e.message)}}

function showMini(){
 openModal(`<div class="result"><div class="game-icon">⚡</div><h2>VLDST RUSH</h2><p class="muted">Нажимай на цели, собирай комбо и набирай очки.</p><div class="rush-hud"><div class="rush-stat">⏱️<b id="rushTime">20</b><span>сек</span></div><div class="rush-stat">🎯<b id="rushScore">0</b><span>очки</span></div><div class="rush-stat">🔥<b id="rushCombo">0</b><span>комбо</span></div></div><div class="rush-board" id="rushBoard"><div class="muted" style="padding:130px 20px">Нажми «Старт»</div></div><div class="combo" id="rushMsg">Лучший результат — играй ещё!</div><button class="primary" id="rushStart" onclick="startRush()">⚡ СТАРТ</button></div>`);
}
function startRush(){
 clearInterval(miniTimer);let time=20,score=0,combo=0,playing=true;const board=$('rushBoard'),t=$('rushTime'),s=$('rushScore'),c=$('rushCombo'),msg=$('rushMsg'),btn=$('rushStart');if(!board)return;
 btn.disabled=true;btn.textContent='ИДЁТ ИГРА';board.innerHTML='';function spawn(){if(!playing)return;const el=document.createElement('button');el.className='rush-target';el.textContent='✦';el.style.left=`${8+Math.random()*76}%`;el.style.top=`${8+Math.random()*72}%`;el.onclick=()=>{score+=10+Math.min(combo,20)*2;combo++;s.textContent=score;c.textContent=combo;el.remove();spawn()};board.appendChild(el);setTimeout(()=>{if(el.isConnected){el.remove();combo=0;c.textContent=0;spawn()}},1100)}
 spawn();miniTimer=setInterval(()=>{time--;t.textContent=time;if(time<=0){playing=false;clearInterval(miniTimer);board.innerHTML='<div class="muted" style="padding:130px 20px">Игра окончена 🎉</div>';btn.disabled=false;btn.textContent='ИГРАТЬ ЕЩЁ';msg.textContent=`Результат: ${score} очков`;finishRush(score)}},1000);
}
async function finishRush(score){try{const d=await post('/api/minigame/play',{score});toast(`🎉 +${Number(d.reward||0).toLocaleString()} Coins`);await loadUser()}catch(e){toast(e.message)}}

function openCases(){const s=$('casesSection');s?.scrollIntoView({behavior:'smooth',block:'start'})}
function showTelegramRequired(){openModal('<div class="result"><div class="game-icon">📱</div><h2>VLDST CASE</h2><p class="muted">Приложение необходимо открыть через Telegram.</p><button class="primary" onclick="closeModal()">ПОНЯТНО</button></div>')}
async function load(){if(!tg?.initData){showTelegramRequired();return}await loadUser();await loadCases()}
load();
