/* VLDST CASE — mobile Mini App */
"use strict";

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.enableClosingConfirmation?.();
}

const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const ASSET_FALLBACK = window.VLDST_ASSETS.item("VLDST", "common", 1);
let opening = false;
let rushTimer = null;
let rushScore = 0;
let rushStarted = false;

function imageSrc(src, type = "item", label = "VLDST", rarity = "common", seed = 1) {
  if (src && String(src).trim()) return src;
  const a = window.VLDST_ASSETS;
  if (type === "case") return a.case(label, seed);
  if (type === "premium") return a.premium(label);
  if (type === "boost") return a.boost(label);
  if (type === "game") return a.game(label);
  if (type === "task") return a.task(label);
  if (type === "ref") return a.ref(label);
  return a.item(label, rarity, seed);
}

function img(src, cls = "", type = "item", label = "VLDST", rarity = "common", seed = 1) {
  const safe = esc(imageSrc(src, type, label, rarity, seed));
  return `<img class="${cls}" src="${safe}" loading="lazy" alt="${esc(label)}"
    onerror="this.onerror=null;this.src='${ASSET_FALLBACK}'">`;
}

function toast(text) {
  const e = $("toast");
  if (!e) return;
  e.textContent = text;
  e.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => e.classList.remove("show"), 2600);
}

function authHeaders(extra = {}) {
  return {
    "Content-Type": "application/json",
    "X-Telegram-Init-Data": tg?.initData || "",
    ...extra
  };
}

async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: authHeaders(options.headers || {})
    });
  } catch {
    throw new Error("Сервер недоступен. Попробуй ещё раз.");
  }

  let data = {};
  try { data = await response.json(); } catch {}

  if (!response.ok) {
    if (response.status === 401 || data.error === "unauthorized") {
      throw new Error("Открой VLDST CASE через Telegram");
    }
    if (response.status === 403) {
      throw new Error(data.error === "banned" ? "Ваш аккаунт заблокирован" : "Доступ запрещён");
    }

    const messages = {
      not_enough_coins: "Недостаточно Coins",
      case_not_found: "Кейс не найден",
      case_has_no_items: "В кейсе нет предметов",
      already_claimed: "Награда уже получена",
      task_not_found: "Задание не найдено",
      item_not_found: "Предмет уже продан или не найден",
      user_not_found: "Пользователь не найден",
      payment_unavailable: "Оплата сейчас недоступна",
      product_not_found: "Товар не найден",
      invoice_failed: "Не удалось создать оплату",
      server_error: "Ошибка сервера"
    };

    throw new Error(messages[data.error] || data.message || data.error || `Ошибка ${response.status}`);
  }

  return data;
}

function checkAuth() {
  return Boolean(tg?.initData);
}

function openModal(content, options = {}) {
  const modal = $("modal");
  const sheet = $("sheet");
  if (!modal || !sheet) return;

  sheet.innerHTML = content;
  modal.classList.add("open");
  if (options.large) sheet.classList.add("sheet-large");
  else sheet.classList.remove("sheet-large");
  tg?.BackButton?.show();
}

function closeModal() {
  if (rushTimer) {
    clearInterval(rushTimer);
    rushTimer = null;
  }
  rushStarted = false;
  $("modal")?.classList.remove("open");
  tg?.BackButton?.hide();
}

$("modal")?.addEventListener("click", (event) => {
  if (event.target.id === "modal") closeModal();
});
tg?.BackButton?.onClick(closeModal);

function setNav(button) {
  document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
  button?.classList.add("active");
}

function goHome(button) {
  window.scrollTo({ top: 0, behavior: "smooth" });
  setNav(button);
}

async function loadUser() {
  try {
    const user = await api("/api/user");

    if (user.banned) {
      openModal(`
        <div class="result">
          ${img(null, "result-img", "item", "BLOCKED", "mythic", 99)}
          <h2>АККАУНТ ЗАБЛОКИРОВАН</h2>
          <p class="muted">Доступ к VLDST CASE ограничен.</p>
        </div>
      `);
      return user;
    }

    $("balance").textContent =
      `🪙 ${Number(user.coins || 0).toLocaleString()}  ⭐ ${Number(user.stars || 0).toLocaleString()}`;

    $("name").textContent = user.first_name || "Игрок";
    const level = Number(user.level || 1);
    const xp = Number(user.xp || 0);
    $("level").textContent = `Уровень ${level} • ${xp.toLocaleString()} XP`;

    const levelStart = (level - 1) * 100;
    const progress = Math.max(0, Math.min(100, xp - levelStart));
    $("xpbar").style.width = `${progress}%`;
    $("premium").textContent = user.premium_until ? "👑 PREMIUM" : "FREE";

    return user;
  } catch (error) {
    console.error(error);
    toast(error.message);
    return null;
  }
}

async function loadCases() {
  try {
    const data = await api("/api/cases");
    const cases = Array.isArray(data.cases) ? data.cases : [];

    $("caseCount").textContent = `${cases.length} кейсов`;

    $("cases").innerHTML = cases.map((item, index) => `
      <article class="card case-card">
        <button class="case-open" onclick="caseInfo(${Number(item.id)})">
          ${img(item.image_url, "case-img", "case", item.name, "common", index + 1)}
          <div class="case-body">
            <b>${esc(item.name)}</b>
            <div class="case-price">
              <span class="price">🪙 ${Number(item.price_coins || 0).toLocaleString()}</span>
              <span class="pill">ОТКРЫТЬ</span>
            </div>
          </div>
        </button>
      </article>
    `).join("") || `
      <div class="card empty-card">
        <b>Кейсов пока нет</b>
        <p class="muted">Попробуй обновить приложение.</p>
      </div>
    `;

    await loadItems(cases);
  } catch (error) {
    console.error(error);
    toast("Не удалось загрузить кейсы");
  }
}

async function loadItems(cases) {
  const allItems = [];

  for (const currentCase of cases) {
    try {
      const data = await api(`/api/cases/${currentCase.id}/items`);
      if (Array.isArray(data.items)) allItems.push(...data.items);
    } catch (error) {
      console.warn(error);
    }
  }

  const seen = new Set();
  const unique = allItems.filter((item) => {
    const key = item.id ?? `${item.name}-${item.rarity}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 60);

  $("itemCount").textContent = `${unique.length} шт.`;

  $("items").innerHTML = unique.map((item, index) => {
    const rarity = String(item.rarity || "common").toLowerCase();
    return `
      <article class="item ${esc(rarity)}">
        ${img(item.image_url, "", "item", item.name, rarity, index + 1)}
        <span>${esc(item.name)}</span>
      </article>
    `;
  }).join("") || `<p class="muted">Предметов пока нет.</p>`;
}

async function caseInfo(id) {
  try {
    const [cases, data] = await Promise.all([
      api("/api/cases"),
      api(`/api/cases/${id}/items`)
    ]);

    const current = (cases.cases || []).find((x) => Number(x.id) === Number(id));
    if (!current) {
      toast("Кейс не найден");
      return;
    }

    const items = data.items || [];

    openModal(`
      <div class="case-modal-head">
        ${img(current.image_url, "modal-case-img", "case", current.name, "common", Number(id) || 1)}
        <div>
          <span class="premium-tag">VLDST CASE</span>
          <h2>${esc(current.name)}</h2>
          <p class="muted">${esc(current.description || "Эксклюзивная коллекция VLDST.")}</p>
        </div>
      </div>

      <div class="case-note">✓ Награды выдаются по фиксированной последовательности. Без случайных платных лутбоксов.</div>

      <div class="price-grid">
        <button class="primary" onclick="openCase(${Number(id)})">
          🪙 ${Number(current.price_coins || 0).toLocaleString()}
        </button>
        <button class="primary stars-btn" onclick="buyCase(${Number(id)})">
          ⭐ ${Number(current.price_stars || 0)}
        </button>
      </div>

      <h3>🎁 Предметы кейса</h3>
      <div class="item-grid">
        ${items.map((item, index) => {
          const rarity = String(item.rarity || "common").toLowerCase();
          return `
            <article class="item ${esc(rarity)}">
              ${img(item.image_url, "", "item", item.name, rarity, index + 1)}
              <span>${esc(item.name)}</span>
            </article>
          `;
        }).join("") || `<p class="muted">Предметов пока нет.</p>`}
      </div>
    `);
  } catch (error) {
    toast(error.message);
  }
}

function buildReel(items, selected) {
  const list = [];
  for (let i = 0; i < 14; i++) list.push(items[i % items.length]);
  list.push(selected);

  return `
    <div class="reel-window">
      <div class="reel-pointer"></div>
      <div class="reel-track" id="reelTrack">
        ${list.map((item, index) => {
          const rarity = String(item.rarity || "common").toLowerCase();
          return `
            <div class="reel-item ${esc(rarity)}">
              ${img(item.image_url, "", "item", item.name, rarity, index + 1)}
              <b>${esc(item.name)}</b>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

async function openCase(id) {
  if (opening) return;
  opening = true;

  try {
    const data = await api(`/api/cases/${id}/open`, { method: "POST" });
    if (!data.item) throw new Error("Не удалось получить предмет");

    // Get the case list for a convincing visual reel.
    let reelItems = [data.item];
    try {
      const list = await api(`/api/cases/${id}/items`);
      if (Array.isArray(list.items) && list.items.length) reelItems = list.items;
    } catch {}

    openModal(`
      <div class="result">
        <div class="win-ring">✦</div>
        <h2>ОТКРЫТИЕ КЕЙСА</h2>
        <p class="muted">Лента останавливается на твоей награде</p>
        ${buildReel(reelItems, data.item)}
        <div id="caseResult" class="case-result hidden"></div>
      </div>
    `, { large: true });

    const track = $("reelTrack");
    const itemWidth = 122;
    const finalIndex = 14;
    if (track) {
      const offset = -(finalIndex * itemWidth - 65);
      requestAnimationFrame(() => {
        track.style.transform = `translateX(${offset}px)`;
      });
    }

    await new Promise((resolve) => setTimeout(resolve, 2400));

    const rarity = String(data.item.rarity || "common").toLowerCase();
    const result = $("caseResult");
    if (result) {
      result.classList.remove("hidden");
      result.innerHTML = `
        ${img(data.item.image_url, "result-img", "item", data.item.name, rarity, 77)}
        <h2>${esc(data.item.name)}</h2>
        <p class="rarity-${esc(rarity)}">${esc(data.item.rarity || "COMMON")}</p>
        <p class="muted">Цена продажи: 🪙 ${Number(data.item.sell_price || 0).toLocaleString()}</p>
        <button class="primary" onclick="closeModal();load()">ЗАБРАТЬ</button>
      `;
    }

    await loadUser();
  } catch (error) {
    toast(error.message);
  } finally {
    opening = false;
  }
}

function openInvoice(invoiceUrl) {
  if (!invoiceUrl) {
    toast("Ссылка оплаты не создана");
    return;
  }

  if (tg && typeof tg.openInvoice === "function") {
    tg.openInvoice(invoiceUrl, (status) => {
      if (status === "paid") {
        toast("⭐ Оплата успешна!");
        setTimeout(load, 800);
      } else if (status === "cancelled") {
        toast("Оплата отменена");
      } else if (status === "failed") {
        toast("Оплата не прошла");
      }
    });
  } else {
    window.open(invoiceUrl, "_blank", "noopener");
  }
}

async function buyCase(id) {
  try {
    const data = await api("/api/stars/invoice", {
      method: "POST",
      body: JSON.stringify({ kind: "case", case_id: id })
    });
    openInvoice(data.invoice_url);
  } catch (error) {
    toast(error.message);
  }
}

function productRow(product, kind, type) {
  const image = imageSrc(null, type, product.title || "VLDST", "epic", 15);
  return `
    <div class="card shop-row">
      <img class="shop-img" src="${esc(image)}" alt="${esc(product.title || "VLDST")}">
      <div class="shop-copy">
        <b>${esc(product.title)}</b>
        <div class="muted">${esc(product.description || "")}</div>
      </div>
      <button class="primary small" onclick="buyProduct('${esc(product.id)}','${esc(kind)}')">
        ⭐ ${Number(product.stars || 0)}
      </button>
    </div>
  `;
}

async function showShop() {
  openModal(`
    <h2>⭐ Магазин VLDST</h2>
    <p class="muted">Telegram Stars → внутренняя валюта, Premium и бусты.</p>
    <div id="shoplist"><div class="loading">Загрузка...</div></div>
  `);

  try {
    const data = await api("/api/shop");
    const balanceProducts = data.balance_products || [];
    const storeProducts = data.store_products || [];

    $("shoplist").innerHTML = `
      <h3>⭐ Внутренние Stars</h3>
      ${balanceProducts.map((p) => productRow(p, "balance", "premium")).join("") || `<p class="muted">Нет наборов.</p>`}

      <h3>👑 Premium</h3>
      ${storeProducts.filter((p) => p.type === "premium")
        .map((p) => productRow(p, "store", "premium")).join("") || `<p class="muted">Premium пока нет.</p>`}

      <h3>⚡ Бусты</h3>
      ${storeProducts.filter((p) => p.type !== "premium")
        .map((p) => productRow(p, "store", "boost")).join("") || `<p class="muted">Бустов пока нет.</p>`}
    `;
  } catch (error) {
    toast(error.message);
  }
}

async function buyProduct(id, kind) {
  try {
    const data = await api("/api/stars/invoice", {
      method: "POST",
      body: JSON.stringify({ kind, product: id })
    });
    openInvoice(data.invoice_url);
  } catch (error) {
    toast(error.message);
  }
}

function showMini() {
  openModal(`
    <div class="result">
      ${img(null, "result-img", "game", "VLDST RUSH")}
      <h2>VLDST RUSH</h2>
      <p class="muted">7 секунд. Нажимай на кнопку как можно быстрее.</p>

      <div class="rush-panel">
        <div class="rush-stats">
          <span>⏱ <b id="rushTime">7.0</b></span>
          <span>⚡ <b id="rushScore">0</b></span>
        </div>
        <button id="rushButton" class="rush-button" onclick="tapRush()" disabled>НАЧАТЬ</button>
        <button id="rushStart" class="primary" onclick="startRush()">▶ СТАРТ</button>
        <div id="game"></div>
      </div>
    </div>
  `);
}

function startRush() {
  if (rushStarted) return;
  rushStarted = true;
  rushScore = 0;

  const button = $("rushButton");
  const start = $("rushStart");
  if (button) {
    button.disabled = false;
    button.textContent = "TAP!";
  }
  if (start) start.disabled = true;

  let left = 7.0;
  $("rushTime").textContent = left.toFixed(1);
  $("rushScore").textContent = "0";

  const startedAt = performance.now();
  rushTimer = setInterval(() => {
    left = Math.max(0, 7 - (performance.now() - startedAt) / 1000);
    if ($("rushTime")) $("rushTime").textContent = left.toFixed(1);

    if (left <= 0) finishRush();
  }, 50);
}

function tapRush() {
  if (!rushStarted) return;
  rushScore = Math.min(40, rushScore + 1);
  $("rushScore").textContent = String(rushScore);
}

async function finishRush() {
  if (!rushStarted) return;
  rushStarted = false;
  clearInterval(rushTimer);
  rushTimer = null;

  const button = $("rushButton");
  if (button) button.disabled = true;

  try {
    const data = await api("/api/minigame/play", {
      method: "POST",
      body: JSON.stringify({ score: rushScore })
    });

    $("game").innerHTML = `
      <div class="game-result">
        <b>Результат: ${Number(data.score || 0)} taps</b>
        <strong>+${Number(data.reward || 0).toLocaleString()} 🪙</strong>
        <span class="muted">Попробуй побить свой результат.</span>
      </div>
      <button class="primary small restart-rush" onclick="startRush()">↻ ЕЩЁ РАЗ</button>
    `;
    await loadUser();
  } catch (error) {
    toast(error.message);
  }
}

async function showRef() {
  try {
    const data = await api("/api/referrals");
    openModal(`
      <div class="result">
        ${img(null, "result-img", "ref", "REFERRALS")}
        <h2>РЕФЕРАЛЫ</h2>
        <p>Приглашено: <b>${Number(data.count || 0)}</b></p>
        <p>Заработано: <b>${Number(data.earned || 0).toLocaleString()} 🪙</b></p>
        <p class="muted">За нового игрока — 500 Coins.</p>
        <input id="refLink" value="${esc(data.referral_link || "")}" readonly>
        <button class="primary" onclick="copyReferral()">🔗 КОПИРОВАТЬ</button>
        <button class="primary secondary-btn" onclick="shareReferral()">📤 ПРИГЛАСИТЬ</button>
      </div>
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function copyReferral() {
  const input = $("refLink");
  if (!input) return;

  try {
    await navigator.clipboard.writeText(input.value);
  } catch {
    input.select();
    document.execCommand("copy");
  }
  toast("Ссылка скопирована");
}

function shareReferral() {
  const input = $("refLink");
  if (!input) return;

  const text = encodeURIComponent("🎁 Заходи в VLDST CASE и получай Coins!");
  const url = encodeURIComponent(input.value);
  const share = `https://t.me/share/url?url=${url}&text=${text}`;

  if (tg?.openTelegramLink) tg.openTelegramLink(share);
  else window.open(share, "_blank", "noopener");
}

async function showTasks() {
  try {
    const data = await api("/api/tasks");
    openModal(`
      <h2>🎯 Задания</h2>
      <p class="muted">Выполняй задания и повышай уровень.</p>
      ${(data.tasks || []).map((task) => `
        <div class="card task-row">
          <div>
            <b>${esc(task.title)}</b>
            <p class="muted">${esc(task.description || "")}</p>
            <span class="price">
              🪙 ${Number(task.reward_coins || 0).toLocaleString()}
              ${task.reward_stars ? ` • ⭐ ${Number(task.reward_stars)}` : ""}
            </span>
          </div>
          <button class="primary small" onclick="claim(${Number(task.id)})" ${task.claimed ? "disabled" : ""}>
            ${task.claimed ? "✓ ПОЛУЧЕНО" : "ЗАБРАТЬ"}
          </button>
        </div>
      `).join("") || `<p class="muted">Новых заданий нет.</p>`}
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function claim(id) {
  try {
    const data = await api(`/api/tasks/${id}/claim`, { method: "POST" });
    toast(`🎁 +${Number(data.reward_coins || 0).toLocaleString()} Coins`);
    await loadUser();
    await showTasks();
  } catch (error) {
    toast(error.message);
  }
}

async function showInventory() {
  try {
    const data = await api("/api/inventory");
    const inventory = data.inventory || [];

    openModal(`
      <h2>🎒 Инвентарь</h2>
      <div class="inventory-head">
        <p class="muted">Предметы можно продать за Coins.</p>
        <span class="pill">${inventory.length} шт.</span>
      </div>
      <div class="item-grid inventory-grid">
        ${inventory.map((item, index) => {
          const rarity = String(item.rarity || "common").toLowerCase();
          return `
            <article class="item ${esc(rarity)} inventory-item">
              ${img(item.image_url, "", "item", item.name, rarity, index + 1)}
              <span>
                <b>${esc(item.name)}</b>
                <small>${esc(item.rarity || "COMMON")}</small>
                <button class="pill sell-btn" onclick="sell(${Number(item.inventory_id)})">
                  🪙 ${Number(item.sell_price || 0).toLocaleString()} ПРОДАТЬ
                </button>
              </span>
            </article>
          `;
        }).join("") || `<div class="empty-card"><p class="muted">Инвентарь пуст. Открой первый кейс!</p></div>`}
      </div>
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function sell(id) {
  try {
    const data = await api(`/api/inventory/${id}/sell`, { method: "POST" });
    toast(`Продано за ${Number(data.sold_for || 0).toLocaleString()} Coins`);
    await loadUser();
    await showInventory();
  } catch (error) {
    toast(error.message);
  }
}

async function showProfile() {
  try {
    const user = await api("/api/user");
    const name = user.first_name || "Игрок";
    const initials = name.trim().slice(0, 1).toUpperCase();

    openModal(`
      <div class="profile-modal">
        <div class="avatar big">${esc(initials)}</div>
        <h2>${esc(name)}</h2>
        <p class="muted">
          ${user.username ? `@${esc(user.username)}` : "@player"}
          • ID ${esc(user.telegram_id)}
        </p>

        <div class="profile-stats">
          <div>🪙<b>${Number(user.coins || 0).toLocaleString()}</b><small>Coins</small></div>
          <div>⭐<b>${Number(user.stars || 0).toLocaleString()}</b><small>Stars</small></div>
          <div>🏆<b>${Number(user.level || 1)}</b><small>Level</small></div>
          <div>⚡<b>${Number(user.xp || 0).toLocaleString()}</b><small>XP</small></div>
        </div>

        <div class="premium-box">
          ${user.premium_until ? `👑 Premium активно до ${new Date(user.premium_until).toLocaleDateString()}` : "FREE аккаунт"}
        </div>

        <div class="grid">
          <button class="primary" onclick="showInventory()">🎒 Инвентарь</button>
          <button class="primary" onclick="showLeaderboard()">🏆 Рейтинг</button>
        </div>
        <button class="primary secondary-btn" onclick="showTasks()">🎯 Мои задания</button>
      </div>
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function showLeaderboard() {
  try {
    const data = await api("/api/leaderboard");

    openModal(`
      <h2>🏆 Рейтинг</h2>
      <p class="muted">Топ игроков по XP.</p>
      ${(data.leaderboard || []).map((user, index) => `
        <div class="rank-row ${index < 3 ? "top-rank" : ""}">
          <b>${index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : "#" + (index + 1)}</b>
          <span>${esc(user.first_name || "Игрок")} ${user.username ? `<small>@${esc(user.username)}</small>` : ""}</span>
          <strong>LVL ${Number(user.level || 1)}</strong>
          <span>${Number(user.xp || 0).toLocaleString()} XP</span>
        </div>
      `).join("") || `<p class="muted">Рейтинг пока пуст.</p>`}
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function showBoosts() {
  try {
    const data = await api("/api/boosts");

    openModal(`
      <h2>⚡ Мои бусты</h2>
      ${(data.boosts || []).map((boost) => `
        <div class="card boost-row">
          <img class="boost-mini" src="${esc(window.VLDST_ASSETS.boost(boost.type || "BOOST"))}" alt="boost">
          <div>
            <b>⚡ ${esc(boost.type || "BOOST")}</b>
            <div class="muted">До: ${boost.expires_at ? new Date(boost.expires_at).toLocaleString() : "—"}</div>
          </div>
        </div>
      `).join("") || `<p class="muted">Активных бустов нет.</p>`}
      <button class="primary" onclick="showShop()">⭐ ОТКРЫТЬ МАГАЗИН</button>
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function claimDaily() {
  try {
    const data = await api("/api/daily", { method: "POST" });
    toast(`🎁 +${Number(data.reward || 0).toLocaleString()} Coins`);
    await loadUser();
  } catch (error) {
    toast(error.message === "Награда уже получена"
      ? "⏳ Сегодня награда уже получена"
      : error.message);
  }
}

function openCases(button) {
  $("casesSection")?.scrollIntoView({ behavior: "smooth", block: "start" });
  setNav(button);
}

function showTelegramRequired() {
  openModal(`
    <div class="result">
      ${img(null, "result-img", "item", "TELEGRAM", "rare", 42)}
      <h2>VLDST CASE</h2>
      <p class="muted">Открой приложение через кнопку бота в Telegram.</p>
      <button class="primary" onclick="closeModal()">ПОНЯТНО</button>
    </div>
  `);
}

async function load() {
  if (!checkAuth()) {
    showTelegramRequired();
    return;
  }

  await Promise.allSettled([loadUser(), loadCases()]);
}

load();
