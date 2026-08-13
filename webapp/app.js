/* VLDST CASE — frontend. All standard artwork is embedded in assets.js. */
"use strict";

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.enableClosingConfirmation?.();
}

const $ = (id) => document.getElementById(id);
const ASSET_FALLBACK = window.VLDST_ASSETS.item("VLDST", "common", 1);

const esc = (v) => String(v ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function attr(v) { return esc(v); }

function imageSrc(src, type = "item", label = "VLDST", rarity = "common", seed = 1) {
  if (src && String(src).trim()) return src;
  if (type === "case") return window.VLDST_ASSETS.case(label, seed);
  if (type === "premium") return window.VLDST_ASSETS.premium(label);
  if (type === "boost") return window.VLDST_ASSETS.boost(label);
  if (type === "game") return window.VLDST_ASSETS.game(label);
  if (type === "task") return window.VLDST_ASSETS.task(label);
  if (type === "ref") return window.VLDST_ASSETS.ref(label);
  return window.VLDST_ASSETS.item(label, rarity, seed);
}

function img(src, cls = "", type = "item", label = "VLDST", rarity = "common", seed = 1) {
  const safe = attr(imageSrc(src, type, label, rarity, seed));
  return `<img class="${cls}" src="${safe}" loading="lazy" alt="${attr(label)}"
    onerror="this.onerror=null;this.src='${ASSET_FALLBACK}'">`;
}

function toast(text) {
  const e = $("toast");
  if (!e) return;
  e.textContent = text;
  e.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => e.classList.remove("show"), 2500);
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
    throw new Error("Сервер недоступен. Проверь запуск Flask.");
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
      user_not_found: "Пользователь не найден",
      invalid_telegram_data: "Не удалось проверить Telegram",
      payment_unavailable: "Оплата сейчас недоступна"
    };

    throw new Error(messages[data.error] || data.message || data.error || `Ошибка ${response.status}`);
  }

  return data;
}

function checkAuth() {
  return Boolean(tg?.initData);
}

function openModal(content) {
  const modal = $("modal");
  const sheet = $("sheet");
  if (!modal || !sheet) return;
  sheet.innerHTML = content;
  modal.classList.add("open");
  tg?.BackButton?.show();
}

function closeModal() {
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
    $("level").textContent =
      `Уровень ${Number(user.level || 1)} • ${Number(user.xp || 0).toLocaleString()} XP`;

    const xp = Number(user.xp || 0);
    $("xpbar").style.width = `${Math.min(100, xp % 100)}%`;
    $("premium").textContent = user.premium_until ? "👑 PREMIUM" : "FREE";

    return user;
  } catch (error) {
    console.error(error);
    toast(error.message);
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
        <p class="muted">Добавь кейсы в базе данных — изображения подставятся автоматически.</p>
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
  const unique = allItems
    .filter((item) => {
      const key = item.id ?? `${item.name}-${item.rarity}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 49);

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
    const cases = await api("/api/cases");
    const current = (cases.cases || []).find((x) => Number(x.id) === Number(id));

    if (!current) {
      toast("Кейс не найден");
      return;
    }

    const data = await api(`/api/cases/${id}/items`);
    const items = data.items || [];

    openModal(`
      <div class="case-modal-head">
        ${img(current.image_url, "modal-case-img", "case", current.name, "common", Number(id) || 1)}
        <div>
          <h2>${esc(current.name)}</h2>
          <p class="muted">${esc(current.description || "Эксклюзивный кейс VLDST CASE")}</p>
        </div>
      </div>

      <div class="price-grid">
        <button class="primary" onclick="openCase(${Number(id)})">
          🪙 ${Number(current.price_coins || 0).toLocaleString()}
        </button>
        <button class="primary stars-btn" onclick="buyCase(${Number(id)})">
          ⭐ ${Number(current.price_stars || 0)}
        </button>
      </div>

      <h3>🎁 Содержимое</h3>

      <div class="item-grid">
        ${items.map((item, index) => {
          const rarity = String(item.rarity || "common").toLowerCase();
          return `
            <article class="item ${esc(rarity)}">
              ${img(item.image_url, "", "item", item.name, rarity, index + 1)}
              <span>${esc(item.name)}</span>
            </article>
          `;
        }).join("") || `<p class="muted">Предметов в кейсе пока нет.</p>`}
      </div>
    `);
  } catch (error) {
    toast(error.message);
  }
}

async function openCase(id) {
  try {
    closeModal();
    toast("🎁 Открываем кейс...");

    const data = await api(`/api/cases/${id}/open`, { method: "POST" });

    if (!data.item) {
      toast("Не удалось получить предмет");
      return;
    }

    const rarity = String(data.item.rarity || "common").toLowerCase();

    openModal(`
      <div class="result win">
        <div class="win-ring">✦</div>
        <h2>ВЫИГРЫШ!</h2>
        ${img(data.item.image_url, "result-img", "item", data.item.name, rarity, 77)}
        <h2>${esc(data.item.name)}</h2>
        <p class="rarity-${esc(rarity)}">${esc(data.item.rarity || "COMMON")}</p>
        <p class="muted">Продажа: 🪙 ${Number(data.item.sell_price || 0).toLocaleString()}</p>
        <button class="primary" onclick="closeModal();load()">ЗАБРАТЬ</button>
      </div>
    `);

    await loadUser();
  } catch (error) {
    toast(error.message);
  }
}

function openInvoice(invoiceUrl) {
  if (!invoiceUrl) {
    toast("Ссылка оплаты не создана");
    return;
  }

  if (tg && typeof tg.openInvoice === "function") {
    tg.openInvoice(invoiceUrl, (status) => {
      console.log("Payment:", status);

      if (status === "paid") {
        toast("⭐ Оплата успешна!");
        setTimeout(load, 700);
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

function productRow(product, kind, type = "premium") {
  const image = imageSrc(null, type, product.title || "VLDST", "epic", 15);
  return `
    <div class="card shop-row">
      <img class="shop-img" src="${attr(image)}" alt="${attr(product.title || "VLDST")}">
      <div class="shop-copy">
        <b>${esc(product.title)}</b>
        <div class="muted">${esc(product.description || "")}</div>
      </div>
      <button class="primary small" onclick="buyProduct('${attr(product.id)}','${attr(kind)}')">
        ⭐ ${Number(product.stars || 0)}
      </button>
    </div>
  `;
}

async function showShop() {
  openModal(`
    <h2>⭐ Магазин VLDST</h2>
    <p class="muted">Telegram Stars • Premium • бусты</p>
    <div id="shoplist"><div class="loading">Загрузка...</div></div>
  `);

  try {
    const data = await api("/api/shop");
    const balanceProducts = data.balance_products || [];
    const storeProducts = data.store_products || [];

    $("shoplist").innerHTML = `
      <h3>⭐ Пополнение</h3>
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

async function showMini() {
  openModal(`
    <div class="result">
      ${img(null, "result-img", "game", "VLDST RUSH")}
      <h2>VLDST RUSH</h2>
      <p class="muted">Играй и получай Coins.</p>
      <button class="primary" onclick="play()">⚡ ИГРАТЬ</button>
      <div id="game"></div>
    </div>
  `);
}

async function play() {
  try {
    const data = await api("/api/minigame/play", { method: "POST" });

    $("game").innerHTML = `
      <div class="game-result">
        <b>Счёт: ${Number(data.score || 0)}</b>
        <strong>+${Number(data.reward || 0).toLocaleString()} 🪙</strong>
      </div>
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

        <input id="refLink" value="${attr(data.referral_link || "")}" readonly>

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
      ${(data.tasks || []).map((task) => `
        <div class="card task-row">
          <div>
            <b>${esc(task.title)}</b>
            <p class="muted">${esc(task.description || "")}</p>
            <span class="price">
              🪙 ${Number(task.reward_coins || 0).toLocaleString()}
              ${task.reward_stars ? `⭐ ${Number(task.reward_stars)}` : ""}
            </span>
          </div>
          <button class="primary small" onclick="claim(${Number(task.id)})" ${task.claimed ? "disabled" : ""}>
            ${task.claimed ? "✓" : "ЗАБРАТЬ"}
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
    await api(`/api/tasks/${id}/claim`, { method: "POST" });
    toast("🎁 Награда получена!");
    await loadUser();
    await showTasks();
  } catch (error) {
    toast(error.message);
  }
}

async function showInventory() {
  try {
    const data = await api("/api/inventory");

    openModal(`
      <h2>🎒 Инвентарь</h2>
      <p class="muted">Полученные предметы</p>

      <div class="item-grid">
        ${(data.inventory || []).map((item, index) => {
          const rarity = String(item.rarity || "common").toLowerCase();
          return `
            <article class="item ${esc(rarity)}">
              ${img(item.image_url, "", "item", item.name, rarity, index + 1)}
              <span>
                ${esc(item.name)}
                <br>
                <button class="pill sell-btn" onclick="sell(${Number(item.inventory_id)})">
                  🪙 ${Number(item.sell_price || 0).toLocaleString()} ПРОДАТЬ
                </button>
              </span>
            </article>
          `;
        }).join("") || `<p class="muted">Инвентарь пуст.</p>`}
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

    openModal(`
      <div class="profile-modal">
        <div class="avatar big">V</div>
        <h2>${esc(user.first_name || "Игрок")}</h2>
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
          ${user.premium_until ? "👑 Premium активно" : "FREE аккаунт"}
        </div>

        <div class="grid">
          <button class="primary" onclick="showInventory()">🎒 Инвентарь</button>
          <button class="primary" onclick="showLeaderboard()">🏆 Рейтинг</button>
        </div>
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
      ${(data.leaderboard || []).map((user, index) => `
        <div class="rank-row">
          <b>#${index + 1}</b>
          <span>${esc(user.first_name || "Игрок")} ${user.username ? `@${esc(user.username)}` : ""}</span>
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
      ${(data.boosts || []).map((boost, index) => `
        <div class="card boost-row">
          <img class="boost-mini" src="${attr(window.VLDST_ASSETS.boost(boost.type || "BOOST"))}" alt="boost">
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
      <p class="muted">Приложение необходимо открыть через Telegram.</p>
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
