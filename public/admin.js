let key="";const $=s=>document.querySelector(s);
async function req(url,opt={}){opt.headers={...(opt.headers||{}),'x-admin-key':key,'content-type':'application/json'};return(await fetch(url,opt)).json()}
function tab(name){document.querySelectorAll('.atab').forEach(x=>x.classList.toggle('active',x.dataset.tab===name));document.querySelectorAll('.adminpage').forEach(x=>x.classList.toggle('hidden',x.id!==`page-${name}`))}
async function loadStats(){
 key=$('#key').value.trim();const r=await req('/api/admin/stats');if(!r.ok)return alert(r.error);
 const s=r.stats;$('#dash').innerHTML=`<div class="stats"><div class="stat"><b>${s.users}</b><small>👥 Users</small></div><div class="stat"><b>${s.opens}</b><small>🎁 Openings</small></div><div class="stat"><b>${Number(s.coins).toLocaleString()}</b><small>🪙 Coins</small></div><div class="stat"><b>${s.sold}</b><small>💰 Sold</small></div></div>`;
 tab('dashboard');await Promise.all([loadUsers(),loadShop()]);
}
async function loadUsers(){const r=await req('/api/admin/users');if(!r.ok)return;$('#users').innerHTML=r.users.map(x=>`<div class="task"><div class="row"><b>#${x.id} ${x.first_name||'Player'}</b><span>🪙 ${Number(x.coins).toLocaleString()}</span></div><div class="muted">@${x.username||'-'} · L${x.level} · TG ${x.telegram_id}</div><button class="btn mini" onclick="give(${x.id})">+ Coins</button></div>`).join('')}
async function give(id){const a=prompt('Сколько Coins выдать?');if(!a)return;const r=await req('/api/admin/give-coins',{method:'POST',body:JSON.stringify({userId:id,amount:Number(a)})});alert(r.ok?'Готово':r.error);loadUsers()}
async function promo(){const r=await req('/api/admin/promo',{method:'POST',body:JSON.stringify({code:$('#pc').value,reward:Number($('#pr').value),maxUses:Number($('#pm').value)})});alert(r.ok?'Промокод создан':r.error)}
async function loadShop(){const r=await req('/api/admin/shop');if(!r.ok)return;$('#shop').innerHTML=r.products.map(p=>`<div class="task"><div class="row"><b>${p.title}</b><span>⭐ ${p.stars}</span></div><div class="muted">${p.description} · ${p.kind} · ${p.active?'ACTIVE':'OFF'}</div><div class="row"><button class="btn mini" onclick="price('${p.code}')">Цена</button><button class="btn mini ghost" onclick="toggleShop('${p.code}')">${p.active?'Выключить':'Включить'}</button></div></div>`).join('')}
async function price(code){const a=prompt('Новая цена Stars');if(!a)return;const r=await req('/api/admin/shop/price',{method:'POST',body:JSON.stringify({code,stars:Number(a)})});alert(r.ok?'Цена обновлена':r.error);loadShop()}
async function toggleShop(code){const r=await req('/api/admin/shop/toggle',{method:'POST',body:JSON.stringify({code})});if(!r.ok)return alert(r.error);loadShop()}
