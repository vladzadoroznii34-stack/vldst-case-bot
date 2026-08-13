/* VLDST ADMIN — all standard artwork is embedded in assets.js. */
"use strict";

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const $ = (id) => document.getElementById(id);
const H = () => ({
  "X-Telegram-Init-Data": tg?.initData || "",
  "Content-Type": "application/json"
});

let users = [];

const esc = (v) => String(v ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function toast(text) {
  const e = $("toast");
  if (!e) return;
  e.textContent = text;
  e.classList.add("show");
  clearTimeout(window.__adminToast);
  window.__adminToast = setTimeout(() => e.classList.remove("show"), 2400);
}

async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: { ...H(), ...(options.headers || {}) }
    });
  } catch {
    throw new Error("Сервер недоступен. Проверь Flask.");
  }

  let data = {};
  try { data = await response.json(); } catch {}

  if (!response.ok) {
    if (response.status === 401 || data.error === "unauthorized") {
      throw new Error("Открой ADMIN через Telegram");
    }
    if (response.status === 403) {
      throw new Error("Нет прав администратора");
    }
    throw new Error(data.message || data.error || `Ошибка ${response.status}`);
  }

  return data;
}

function post(url, body) {
  return api(url, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

async function loadAll() {
  try {
    const [stats, userData, caseData] = await Promise.all([
      api("/api/admin/stats"),
      api("/api/admin/users"),
      api("/api/admin/cases")
    ]);

    $("stats").innerHTML = Object.entries(stats || {}).map(([key, value]) => `
      <div class="card stat-card">
        <span class="muted">${esc(key)}</span>
        <h2>${Number(value || 0).toLocaleString()}</h2>
      </div>
    `).join("");

    users = userData.users || [];
    $("userCount").textContent = `${users.length} загружено`;
    renderUsers();

    $("cases").innerHTML = (caseData.cases || []).map((item, index) => `
      <div class="card admin-case-row">
        <img class="admin-case-img" src="${esc(window.VLDST_ASSETS.case(item.name, index + 1))}" alt="case">
        <div class="admin-case-copy">
          <div class="row">
            <b>${esc(item.name)}</b>
            <span class="pill ${item.active ? "active-pill" : "danger"}">${item.active ? "ACTIVE" : "OFF"}</span>
          </div>
          <div class="muted">🪙 ${Number(item.price_coins || 0).toLocaleString()} • ⭐ ${Number(item.price_stars || 0)}</div>
          <button class="primary small" style="margin-top:8px" onclick="toggleCase(${Number(item.id)})">
            ${item.active ? "ОТКЛЮЧИТЬ" : "ВКЛЮЧИТЬ"}
          </button>
        </div>
      </div>
    `).join("") || `<p class="muted">Кейсов нет.</p>`;
  } catch (error) {
    toast(error.message);
  }
}

function renderUsers() {
  const query = ($("search").value || "").trim().toLowerCase();

  const filtered = users
    .filter((user) =>
      String(user.telegram_id).includes(query) ||
      String(user.username || "").toLowerCase().includes(query) ||
      String(user.first_name || "").toLowerCase().includes(query)
    )
    .slice(0, 100);

  $("users").innerHTML = filtered.map((user) => `
    <div class="card user-row">
      <div class="row">
        <b>${esc(user.first_name || "Игрок")}</b>
        <span class="pill ${user.banned ? "danger" : "active-pill"}">
          ${user.banned ? "BAN" : "OK"}
        </span>
      </div>
      <div class="muted">ID ${esc(user.telegram_id)} • @${esc(user.username || "—")}</div>
      <div class="user-balances">
        🪙 ${Number(user.coins || 0).toLocaleString()}
        • ⭐ ${Number(user.stars || 0).toLocaleString()}
        • LVL ${Number(user.level || 1)}
      </div>
      <button class="ghost-btn" onclick="selectUser(${Number(user.telegram_id)})">ВЫБРАТЬ</button>
    </div>
  `).join("") || `<p class="muted">Ничего не найдено.</p>`;
}

function selectUser(id) {
  $("uid").value = id;
  $("uid").focus();
  toast(`Выбран ID ${id}`);
}

function uid() {
  const value = Number($("uid").value);
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error("Введите корректный Telegram ID");
  }
  return value;
}

async function giveCoins() {
  try {
    await post("/api/admin/give-coins", { telegram_id: uid(), amount: 10000 });
    toast("🪙 +10 000 Coins");
    await loadAll();
  } catch (e) { toast(e.message); }
}

async function giveStars() {
  try {
    await post("/api/admin/give-stars", { telegram_id: uid(), amount: 100 });
    toast("⭐ +100 Stars");
    await loadAll();
  } catch (e) { toast(e.message); }
}

async function premium() {
  try {
    await post(`/api/admin/user/${uid()}/premium`, { days: 30 });
    toast("👑 Premium выдан на 30 дней");
    await loadAll();
  } catch (e) { toast(e.message); }
}

async function ban(value) {
  try {
    await post(`/api/admin/user/${uid()}/ban`, { banned: value });
    toast(value ? "⛔ Пользователь заблокирован" : "✅ Пользователь разблокирован");
    await loadAll();
  } catch (e) { toast(e.message); }
}

async function broadcast() {
  try {
    const text = $("broadcastText").value.trim();
    if (!text) {
      toast("Введите текст");
      return;
    }

    const data = await post("/api/admin/broadcast", { text });
    toast(`📢 Отправлено: ${data.sent || 0}, ошибок: ${data.failed || 0}`);
  } catch (e) { toast(e.message); }
}

async function toggleCase(id) {
  try {
    await post(`/api/admin/cases/${id}/toggle`, {});
    toast("Статус кейса изменён");
    await loadAll();
  } catch (e) { toast(e.message); }
}

loadAll();
