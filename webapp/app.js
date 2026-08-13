// ============================================================
// VLDST CASE — MOBILE WEBAPP
// Версия с встроенными SVG-картинками.
// Дополнительные PNG/JPG/WebP для базовой работы не нужны.
// ============================================================

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
    tg.enableClosingConfirmation?.();
}

// ============================================================
// HELPERS
// ============================================================

const $ = (id) => document.getElementById(id);

const ASSET_FALLBACK = svgData(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">
    <rect width="500" height="500" rx="60" fill="#080811"/>
    <circle cx="250" cy="220" r="150" fill="#9142ff" opacity=".14"/>
    <text x="250" y="245" text-anchor="middle"
          fill="#a85aff" font-family="Arial" font-size="80" font-weight="900">V</text>
    <text x="250" y="335" text-anchor="middle"
          fill="#fff" font-family="Arial" font-size="36" font-weight="900">VLDST</text>
    <text x="250" y="370" text-anchor="middle"
          fill="#a85aff" font-family="Arial" font-size="20" font-weight="900">CASE</text>
</svg>
`);

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHtml(value);
}

function telegramInitData() {
    return tg?.initData || "";
}

function authHeaders(extra = {}) {
    return {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": telegramInitData(),
        ...extra
    };
}

// ============================================================
// API
// ============================================================

async function api(url, options = {}) {
    const config = {
        ...options,
        headers: authHeaders(options.headers || {})
    };

    const response = await fetch(url, config);

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        if (response.status === 401 || data.error === "unauthorized") {
            throw new Error("Открой VLDST CASE через Telegram");
        }

        if (response.status === 403) {
            if (data.error === "banned") {
                throw new Error("Ваш аккаунт заблокирован");
            }

            throw new Error("Доступ запрещён");
        }

        const messages = {
            not_enough_coins: "Недостаточно Coins",
            case_not_found: "Кейс не найден",
            case_has_no_items: "В кейсе нет предметов",
            already_claimed: "Награда уже получена",
            task_not_found: "Задание не найдено",
            user_not_found: "Пользователь не найден"
        };

        throw new Error(
            messages[data.error] ||
            data.message ||
            data.error ||
            `Ошибка ${response.status}`
        );
    }

    return data;
}

// ============================================================
// EMBEDDED SVG ART
// ============================================================

function svgData(svg) {
    return "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg);
}

const CASE_THEMES = {
    1: { name: "SHADOW", main: "#7c3cff", second: "#211044", icon: "◆" },
    2: { name: "FIRE", main: "#ff4d22", second: "#4a160d", icon: "🔥" },
    3: { name: "CYBER", main: "#18c8ff", second: "#092d40", icon: "⚡" },
    4: { name: "ROYAL", main: "#ffd43b", second: "#49380c", icon: "♛" },
    5: { name: "MYTHIC", main: "#ff36d1", second: "#46113c", icon: "✦" },
    6: { name: "VLDST", main: "#a94fff", second: "#26103e", icon: "V" }
};

const ITEM_COLORS = {
    common: "#70849a",
    rare: "#4d7cff",
    epic: "#a94fff",
    legendary: "#ff8735",
    mythic: "#ffd32f"
};

function caseImage(id, name = "VLDST CASE") {
    const theme = CASE_THEMES[Number(id)] || CASE_THEMES[6];

    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 520">
        <defs>
            <radialGradient id="bg">
                <stop offset="0" stop-color="${theme.main}" stop-opacity=".38"/>
                <stop offset=".55" stop-color="${theme.second}"/>
                <stop offset="1" stop-color="#05060b"/>
            </radialGradient>

            <linearGradient id="box" x1="0" y1="0" x2="1" y2="1">
                <stop stop-color="${theme.main}"/>
                <stop offset="1" stop-color="${theme.second}"/>
            </linearGradient>

            <filter id="glow">
                <feGaussianBlur stdDeviation="15" result="blur"/>
                <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>

        <rect width="700" height="520" rx="55" fill="url(#bg)"/>

        <circle cx="350" cy="235" r="160"
                fill="${theme.main}" opacity=".13" filter="url(#glow)"/>

        <circle cx="105" cy="100" r="5" fill="${theme.main}"/>
        <circle cx="590" cy="120" r="7" fill="${theme.main}"/>
        <circle cx="620" cy="390" r="4" fill="${theme.main}"/>
        <circle cx="90" cy="390" r="6" fill="${theme.main}"/>

        <g transform="translate(130 180)">
            <rect x="0" y="50" width="440" height="190" rx="25"
                  fill="url(#box)" stroke="${theme.main}" stroke-width="5"/>

            <rect x="20" y="75" width="400" height="140" rx="18"
                  fill="#070811" opacity=".72"/>

            <rect x="205" y="50" width="30" height="190"
                  fill="${theme.main}" opacity=".55"/>

            <rect x="0" y="50" width="440" height="42" rx="20"
                  fill="${theme.main}" opacity=".55"/>

            <rect x="202" y="130" width="36" height="45" rx="7"
                  fill="${theme.main}"/>

            <path d="M210 130 v-18 a10 10 0 0 1 20 0 v18"
                  fill="none" stroke="${theme.main}" stroke-width="8"/>
        </g>

        <circle cx="350" cy="220" r="76"
                fill="#080910" stroke="${theme.main}" stroke-width="4"/>

        <text x="350" y="245" text-anchor="middle"
              font-family="Arial" font-size="62" font-weight="900"
              fill="${theme.main}">${theme.icon}</text>

        <text x="350" y="62" text-anchor="middle"
              fill="#ffffff" font-family="Arial" font-size="29"
              font-weight="900">VLDST CASE</text>

        <text x="350" y="470" text-anchor="middle"
              fill="${theme.main}" font-family="Arial" font-size="25"
              font-weight="900" letter-spacing="4">${escapeHtml(String(name).toUpperCase())}</text>
    </svg>`;

    return svgData(svg);
}

function itemImage(item = {}) {
    const rarity = String(item.rarity || "common").toLowerCase();
    const color = ITEM_COLORS[rarity] || ITEM_COLORS.common;

    const icons = {
        common: "◆",
        rare: "◇",
        epic: "✦",
        legendary: "★",
        mythic: "♛"
    };

    const icon = icons[rarity] || "◆";

    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
        <defs>
            <radialGradient id="bg">
                <stop stop-color="${color}" stop-opacity=".45"/>
                <stop offset=".65" stop-color="#111322"/>
                <stop offset="1" stop-color="#070811"/>
            </radialGradient>

            <filter id="glow">
                <feGaussianBlur stdDeviation="12" result="b"/>
                <feMerge>
                    <feMergeNode in="b"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>

        <rect width="400" height="400" rx="42" fill="url(#bg)"/>

        <circle cx="200" cy="175" r="105"
                fill="${color}" opacity=".14"/>

        <circle cx="200" cy="175" r="75"
                fill="#0a0b13" stroke="${color}" stroke-width="5"
                filter="url(#glow)"/>

        <text x="200" y="202" text-anchor="middle"
              font-family="Arial" font-size="72" font-weight="900"
              fill="${color}">${icon}</text>

        <text x="200" y="315" text-anchor="middle"
              fill="#ffffff" font-family="Arial" font-size="22"
              font-weight="900">VLDST</text>

        <text x="200" y="345" text-anchor="middle"
              fill="${color}" font-family="Arial" font-size="14"
              font-weight="800">${escapeHtml(rarity.toUpperCase())}</text>
    </svg>`;

    return svgData(svg);
}

function premiumImage() {
    return svgData(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">
        <defs>
            <radialGradient id="p">
                <stop stop-color="#ffd43b"/>
                <stop offset=".45" stop-color="#6b4210"/>
                <stop offset="1" stop-color="#080811"/>
            </radialGradient>
        </defs>

        <rect width="500" height="500" rx="60" fill="url(#p)"/>
        <circle cx="250" cy="220" r="130" fill="#ffd43b" opacity=".13"/>

        <text x="250" y="255" text-anchor="middle" font-size="150">👑</text>

        <text x="250" y="350" text-anchor="middle"
              fill="#fff" font-family="Arial" font-size="38"
              font-weight="900">PREMIUM</text>

        <text x="250" y="385" text-anchor="middle"
              fill="#ffd43b" font-family="Arial" font-size="18"
              font-weight="900">VLDST CASE</text>
    </svg>`);
}

function boostImage(type = "BOOST") {
    return svgData(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">
        <defs>
            <radialGradient id="b">
                <stop stop-color="#8c3fff"/>
                <stop offset=".5" stop-color="#26113e"/>
                <stop offset="1" stop-color="#06070d"/>
            </radialGradient>
        </defs>

        <rect width="500" height="500" rx="60" fill="url(#b)"/>
        <circle cx="250" cy="220" r="135"
                fill="#9b45ff" opacity=".16"/>

        <text x="250" y="270" text-anchor="middle" font-size="150">⚡</text>

        <text x="250" y="350" text-anchor="middle"
              fill="#ffffff" font-family="Arial" font-size="30"
              font-weight="900">${escapeHtml(String(type).toUpperCase())}</text>

        <text x="250" y="385" text-anchor="middle"
              fill="#b34fff" font-family="Arial" font-size="18"
              font-weight="900">VLDST</text>
    </svg>`);
}

function gameImage() {
    return svgData(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">
        <defs>
            <radialGradient id="g">
                <stop stop-color="#18c8ff" stop-opacity=".55"/>
                <stop offset=".55" stop-color="#2a1550"/>
                <stop offset="1" stop-color="#06070d"/>
            </radialGradient>
        </defs>

        <rect width="500" height="500" rx="60" fill="url(#g)"/>
        <circle cx="250" cy="210" r="145"
                fill="#18c8ff" opacity=".10"/>

        <text x="250" y="270" text-anchor="middle" font-size="145">🎮</text>

        <text x="250" y="350" text-anchor="middle"
              fill="#fff" font-family="Arial" font-size="34"
              font-weight="900">VLDST RUSH</text>

        <text x="250" y="385" text-anchor="middle"
              fill="#18c8ff" font-family="Arial" font-size="18"
              font-weight="900">PLAY • SCORE • COINS</text>
    </svg>`);
}

function img(src, cls = "", type = "item", data = {}) {
    let image = src;

    if (!image || !String(image).trim()) {
        if (type === "case") {
            image = caseImage(data.id, data.name);
        } else if (type === "premium") {
            image = premiumImage();
        } else if (type === "boost") {
            image = boostImage(data.type);
        } else if (type === "game") {
            image = gameImage();
        } else {
            image = itemImage(data);
        }
    }

    return `
        <img
            class="${cls}"
            src="${escapeAttribute(image)}"
            loading="lazy"
            alt=""
            onerror="this.onerror=null;this.src='${ASSET_FALLBACK}'"
        >
    `;
}

// ============================================================
// TOAST
// ============================================================

function toast(text) {
    const element = $("toast");
    if (!element) return;

    element.textContent = text;
    element.classList.add("show");

    clearTimeout(window.__toastTimer);

    window.__toastTimer = setTimeout(() => {
        element.classList.remove("show");
    }, 2500);
}

// ============================================================
// MODAL
// ============================================================

function openModal(content) {
    const modal = $("modal");
    const sheet = $("sheet");

    if (!modal || !sheet) return;

    sheet.innerHTML = content;
    modal.classList.add("open");

    if (tg?.BackButton) {
        tg.BackButton.show();
    }
}

function closeModal() {
    $("modal")?.classList.remove("open");
    tg?.BackButton?.hide();
}

$("modal")?.addEventListener("click", event => {
    if (event.target.id === "modal") {
        closeModal();
    }
});

// ============================================================
// AUTH
// ============================================================

function checkAuth() {
    return Boolean(tg && tg.initData);
}

function showTelegramRequired() {
    openModal(`
        <div class="result">
            <div class="game-icon">📱</div>
            <h2>VLDST CASE</h2>
            <p class="muted">
                Приложение необходимо открыть через Telegram.
            </p>
            <button class="primary" onclick="closeModal()">
                ПОНЯТНО
            </button>
        </div>
    `);
}

// ============================================================
// USER
// ============================================================

async function loadUser() {
    try {
        const user = await api("/api/user");

        if (!user) return;

        if (user.banned) {
            openModal(`
                <div class="result">
                    <div class="game-icon">⛔</div>
                    <h2>АККАУНТ ЗАБЛОКИРОВАН</h2>
                    <p class="muted">
                        Доступ к VLDST CASE ограничен.
                    </p>
                </div>
            `);
            return user;
        }

        if ($("balance")) {
            $("balance").textContent =
                `🪙 ${Number(user.coins || 0).toLocaleString()} ` +
                `⭐ ${Number(user.stars || 0).toLocaleString()}`;
        }

        if ($("name")) {
            $("name").textContent = user.first_name || "Игрок";
        }

        if ($("level")) {
            $("level").textContent =
                `Уровень ${user.level || 1} • ` +
                `${Number(user.xp || 0).toLocaleString()} XP`;
        }

        if ($("xpbar")) {
            const xp = Number(user.xp || 0);
            $("xpbar").style.width = `${xp % 100}%`;
        }

        if ($("premium")) {
            $("premium").textContent =
                user.premium_until ? "👑 PREMIUM" : "FREE";
        }

        return user;
    } catch (error) {
        console.error(error);
        toast(error.message);
    }
}

// ============================================================
// CASES
// ============================================================

async function loadCases() {
    try {
        const data = await api("/api/cases");
        const container = $("cases");

        if (!container) return;

        const cases = data.cases || [];

        container.innerHTML = cases.map(item => `
            <div class="card case-card">
                <button
                    class="case-open"
                    onclick="caseInfo(${Number(item.id)})"
                >
                    ${img(
                        item.image_url,
                        "case-img",
                        "case",
                        item
                    )}

                    <div class="case-body">
                        <b>${escapeHtml(item.name)}</b>

                        <div class="case-price">
                            <span class="price">
                                🪙 ${Number(item.price_coins || 0).toLocaleString()}
                            </span>

                            <span class="pill">ОТКРЫТЬ</span>
                        </div>
                    </div>
                </button>
            </div>
        `).join("");

        await loadItems(cases);
    } catch (error) {
        console.error(error);
        toast("Не удалось загрузить кейсы");
    }
}

// ============================================================
// ITEMS
// ============================================================

async function loadItems(cases) {
    try {
        const allItems = [];

        for (const currentCase of cases) {
            try {
                const data = await api(
                    `/api/cases/${currentCase.id}/items`
                );

                if (Array.isArray(data.items)) {
                    allItems.push(...data.items);
                }
            } catch (error) {
                console.warn(error);
            }
        }

        const unique = [];
        const ids = new Set();

        for (const item of allItems) {
            if (!ids.has(item.id)) {
                ids.add(item.id);
                unique.push(item);
            }
        }

        const container = $("items");
        if (!container) return;

        container.innerHTML = unique.slice(0, 49).map(item => `
            <div class="item ${String(item.rarity || "common").toLowerCase()}">
                ${img("", "", "item", item)}
                <span>${escapeHtml(item.name)}</span>
            </div>
        `).join("");
    } catch (error) {
        console.error(error);
    }
}

// ============================================================
// CASE INFO
// ============================================================

async function caseInfo(id) {
    try {
        const cases = await api("/api/cases");

        const current = (cases.cases || []).find(
            item => Number(item.id) === Number(id)
        );

        if (!current) {
            toast("Кейс не найден");
            return;
        }

        const data = await api(`/api/cases/${id}/items`);

        openModal(`
            <div class="case-modal-head">
                ${img(
                    current.image_url,
                    "modal-case-img",
                    "case",
                    current
                )}

                <div>
                    <h2>${escapeHtml(current.name)}</h2>
                    <p class="muted">
                        ${escapeHtml(
                            current.description ||
                            "Эксклюзивный кейс VLDST CASE"
                        )}
                    </p>
                </div>
            </div>

            <div class="grid">
                <button class="primary" onclick="openCase(${Number(id)})">
                    🪙 ${Number(current.price_coins || 0).toLocaleString()}
                </button>

                <button class="primary stars-btn" onclick="buyCase(${Number(id)})">
                    ⭐ ${Number(current.price_stars || 0)}
                </button>
            </div>

            <h3>🎁 Содержимое</h3>

            <div class="item-grid">
                ${(data.items || []).map(item => `
                    <div class="item ${String(item.rarity || "common").toLowerCase()}">
                        ${img("", "", "item", item)}
                        <span>${escapeHtml(item.name)}</span>
                    </div>
                `).join("")}
            </div>
        `);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// CASE OPEN — результат сервера + визуальная рулетка
// ============================================================

async function openCase(id) {
    try {
        closeModal();
        toast("🎁 Открываем кейс...");

        const data = await api(
            `/api/cases/${id}/open`,
            { method: "POST" }
        );

        if (!data.item) {
            toast("Не удалось получить предмет");
            return;
        }

        await showCaseRoll(id, data.item);

        await loadUser();
    } catch (error) {
        toast(error.message);
    }
}

async function showCaseRoll(caseId, wonItem) {
    let items = [];

    try {
        const data = await api(`/api/cases/${caseId}/items`);
        items = Array.isArray(data.items) ? data.items : [];
    } catch {
        items = [];
    }

    if (!items.length) {
        showWinResult(wonItem);
        return;
    }

    const pool = [];

    for (let i = 0; i < 24; i++) {
        pool.push(items[Math.floor(Math.random() * items.length)]);
    }

    // Последний предмет — фактический выигрыш с сервера.
    pool.push(wonItem);

    openModal(`
        <div class="result case-roll-result">
            <div class="game-icon">🎁</div>
            <h2>ОТКРЫТИЕ КЕЙСА</h2>

            <div class="roll-window">
                <div class="roll-pointer"></div>
                <div id="caseRollTrack" class="roll-track">
                    ${pool.map(item => `
                        <div class="roll-item ${String(item.rarity || "common").toLowerCase()}">
                            ${img("", "roll-img", "item", item)}
                            <span>${escapeHtml(item.name)}</span>
                        </div>
                    `).join("")}
                </div>
            </div>

            <p class="muted" id="rollStatus">
                Определяем награду...
            </p>
        </div>
    `);

    const track = $("caseRollTrack");

    if (!track) {
        showWinResult(wonItem);
        return;
    }

    const targetIndex = pool.length - 1;
    const target = track.children[targetIndex];

    const itemWidth = target?.getBoundingClientRect().width || 112;
    const gap = 8;

    const viewportWidth =
        track.parentElement?.getBoundingClientRect().width || 320;

    const targetCenter =
        targetIndex * (itemWidth + gap) +
        itemWidth / 2;

    const translate =
        -(targetCenter - viewportWidth / 2);

    track.style.setProperty(
        "--roll-distance",
        `${translate}px`
    );

    // Даем браузеру применить начальное состояние.
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            track.classList.add("rolling");
        });
    });

    setTimeout(() => {
        const status = $("rollStatus");

        if (status) {
            status.textContent = "🎉 Награда определена!";
        }

        setTimeout(() => {
            showWinResult(wonItem);
        }, 650);
    }, 4300);
}

function showWinResult(item) {
    openModal(`
        <div class="result win">
            <div class="win-ring">🎉</div>

            <h2>ВЫИГРЫШ!</h2>

            ${img("", "result-img", "item", item)}

            <h2>${escapeHtml(item.name)}</h2>

            <p class="rarity-${String(
                item.rarity || "common"
            ).toLowerCase()}">
                ${escapeHtml(item.rarity || "COMMON")}
            </p>

            <p class="muted">
                Продажа:
                🪙 ${Number(item.sell_price || 0).toLocaleString()}
            </p>

            <button
                class="primary"
                onclick="closeModal();load()"
            >
                ЗАБРАТЬ
            </button>
        </div>
    `);
}

// ============================================================
// BUY CASE WITH STARS
// ============================================================

async function buyCase(id) {
    try {
        const data = await api(
            "/api/stars/invoice",
            {
                method: "POST",
                body: JSON.stringify({
                    kind: "case",
                    case_id: id
                })
            }
        );

        if (!data.invoice_url) {
            toast("Не удалось создать оплату");
            return;
        }

        openInvoice(data.invoice_url);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// TELEGRAM INVOICE
// ============================================================

function openInvoice(invoiceUrl) {
    if (tg && typeof tg.openInvoice === "function") {
        tg.openInvoice(invoiceUrl, status => {
            console.log("Payment:", status);

            if (status === "paid") {
                toast("⭐ Оплата успешна!");
                setTimeout(load, 800);
            }
        });
    } else {
        window.open(invoiceUrl, "_blank");
    }
}

// ============================================================
// SHOP
// ============================================================

async function showShop() {
    openModal(`
        <h2>⭐ Магазин VLDST</h2>

        <p class="muted">
            Telegram Stars • Premium • бусты
        </p>

        <div id="shoplist">Загрузка...</div>
    `);

    try {
        const data = await api("/api/shop");
        const container = $("shoplist");

        if (!container) return;

        const balanceProducts = data.balance_products || [];
        const storeProducts = data.store_products || [];

        container.innerHTML = `
            <h3>⭐ Пополнение баланса</h3>

            ${balanceProducts.map(product => `
                <div class="card shop-row">
                    <div>
                        <b>${escapeHtml(product.title)}</b>
                        <div class="muted">
                            Stars на баланс VLDST
                        </div>
                    </div>

                    <button
                        class="primary small"
                        onclick="buyProduct(
                            '${escapeAttribute(product.id)}',
                            'balance'
                        )"
                    >
                        ⭐ ${Number(product.stars)}
                    </button>
                </div>
            `).join("")}

            <h3>👑 Premium</h3>

            ${storeProducts.filter(
                p => p.type === "premium"
            ).map(product => `
                <div class="card shop-row">
                    ${img("", "shop-product-img", "premium")}

                    <div>
                        <b>👑 ${escapeHtml(product.title)}</b>
                        <div class="muted">
                            ${escapeHtml(product.description || "")}
                        </div>
                    </div>

                    <button
                        class="primary small"
                        onclick="buyProduct(
                            '${escapeAttribute(product.id)}',
                            'store'
                        )"
                    >
                        ⭐ ${product.stars}
                    </button>
                </div>
            `).join("")}

            <h3>⚡ Бусты</h3>

            ${storeProducts.filter(
                p => p.type !== "premium"
            ).map(product => `
                <div class="card shop-row">
                    ${img(
                        "",
                        "shop-product-img",
                        "boost",
                        { type: product.type }
                    )}

                    <div>
                        <b>⚡ ${escapeHtml(product.title)}</b>
                        <div class="muted">
                            ${escapeHtml(product.description || "")}
                        </div>
                    </div>

                    <button
                        class="primary small"
                        onclick="buyProduct(
                            '${escapeAttribute(product.id)}',
                            'store'
                        )"
                    >
                        ⭐ ${product.stars}
                    </button>
                </div>
            `).join("")}
        `;
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// PRODUCT
// ============================================================

async function buyProduct(id, kind) {
    try {
        const data = await api(
            "/api/stars/invoice",
            {
                method: "POST",
                body: JSON.stringify({
                    kind,
                    product: id
                })
            }
        );

        if (!data.invoice_url) {
            toast("Ссылка оплаты не создана");
            return;
        }

        openInvoice(data.invoice_url);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// MINI GAME
// ============================================================

async function showMini() {
    openModal(`
        <div class="result">
            ${img("", "result-img", "game")}

            <h2>VLDST RUSH</h2>

            <p class="muted">
                Нажимай и набирай очки. За игру получай Coins.
            </p>

            <button class="primary" onclick="play()">
                ⚡ ИГРАТЬ
            </button>

            <div id="game"></div>
        </div>
    `);
}

async function play() {
    try {
        const data = await api(
            "/api/minigame/play",
            { method: "POST" }
        );

        const game = $("game");

        if (game) {
            game.innerHTML = `
                <div class="game-result">
                    <b>
                        Счёт: ${Number(data.score || 0)}
                    </b>

                    <strong>
                        +${Number(
                            data.reward || 0
                        ).toLocaleString()} 🪙
                    </strong>
                </div>
            `;
        }

        await loadUser();
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// REFERRALS
// ============================================================

async function showRef() {
    try {
        const data = await api("/api/referrals");

        openModal(`
            <div class="result">
                <div class="game-icon">👥</div>

                <h2>РЕФЕРАЛЫ</h2>

                <p>
                    Приглашено:
                    <b>${Number(data.count || 0)}</b>
                </p>

                <p>
                    Заработано:
                    <b>
                        ${Number(
                            data.earned || 0
                        ).toLocaleString()} 🪙
                    </b>
                </p>

                <p class="muted">
                    За нового игрока — 500 Coins.
                </p>

                <input
                    id="refLink"
                    value="${escapeAttribute(data.referral_link || "")}"
                    readonly
                >

                <button class="primary" onclick="copyReferral()">
                    🔗 КОПИРОВАТЬ
                </button>

                <button class="primary" onclick="shareReferral()">
                    📤 ПРИГЛАСИТЬ
                </button>
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
        toast("Ссылка скопирована");
    } catch {
        input.select();
        document.execCommand("copy");
        toast("Ссылка скопирована");
    }
}

function shareReferral() {
    const input = $("refLink");
    if (!input) return;

    const text = encodeURIComponent(
        "🎁 Заходи в VLDST CASE и получай Coins!"
    );

    const url = encodeURIComponent(input.value);

    const shareUrl =
        `https://t.me/share/url?url=${url}&text=${text}`;

    if (tg?.openTelegramLink) {
        tg.openTelegramLink(shareUrl);
    } else {
        window.open(shareUrl, "_blank");
    }
}

// ============================================================
// TASKS
// ============================================================

async function showTasks() {
    try {
        const data = await api("/api/tasks");

        openModal(`
            <h2>🎯 Задания</h2>

            ${
                (data.tasks || []).map(task => `
                    <div class="card task-row">
                        <div>
                            <b>${escapeHtml(task.title)}</b>

                            <p class="muted">
                                ${escapeHtml(task.description || "")}
                            </p>

                            <span class="price">
                                🪙 ${Number(
                                    task.reward_coins || 0
                                ).toLocaleString()}

                                ${
                                    task.reward_stars
                                        ? `⭐ ${task.reward_stars}`
                                        : ""
                                }
                            </span>
                        </div>

                        <button
                            class="primary small"
                            onclick="claim(${Number(task.id)})"
                            ${task.claimed ? "disabled" : ""}
                        >
                            ${task.claimed ? "✓" : "ЗАБРАТЬ"}
                        </button>
                    </div>
                `).join("") ||
                `
                    <p class="muted">
                        Новых заданий нет.
                    </p>
                `
            }
        `);
    } catch (error) {
        toast(error.message);
    }
}

async function claim(id) {
    try {
        await api(
            `/api/tasks/${id}/claim`,
            { method: "POST" }
        );

        toast("🎁 Награда получена!");

        await loadUser();
        await showTasks();
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// INVENTORY
// ============================================================

async function showInventory() {
    try {
        const data = await api("/api/inventory");

        openModal(`
            <h2>🎒 Инвентарь</h2>

            <p class="muted">
                Полученные предметы
            </p>

            <div class="item-grid">
                ${
                    (data.inventory || []).map(item => `
                        <div class="item ${
                            String(
                                item.rarity || "common"
                            ).toLowerCase()
                        }">
                            ${img("", "", "item", item)}

                            <span>
                                ${escapeHtml(item.name)}

                                <br>

                                <button
                                    class="pill"
                                    onclick="sell(${Number(item.inventory_id)})"
                                >
                                    🪙 ${Number(
                                        item.sell_price || 0
                                    ).toLocaleString()}
                                    ПРОДАТЬ
                                </button>
                            </span>
                        </div>
                    `).join("") ||
                    `
                        <p class="muted">
                            Инвентарь пуст.
                        </p>
                    `
                }
            </div>
        `);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// SELL
// ============================================================

async function sell(id) {
    try {
        const data = await api(
            `/api/inventory/${id}/sell`,
            { method: "POST" }
        );

        toast(
            `Продано за ${
                Number(
                    data.sold_for || 0
                ).toLocaleString()
            } Coins`
        );

        await loadUser();
        await showInventory();
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// PROFILE
// ============================================================

async function showProfile() {
    try {
        const user = await api("/api/user");

        openModal(`
            <div class="profile-modal">

                <div class="avatar big">V</div>

                <h2>
                    ${escapeHtml(
                        user.first_name || "Игрок"
                    )}
                </h2>

                <p class="muted">
                    ${
                        user.username
                            ? `@${escapeHtml(user.username)}`
                            : "@player"
                    }
                    • ID ${user.telegram_id}
                </p>

                <div class="profile-stats">
                    <div>
                        🪙
                        <b>${Number(
                            user.coins || 0
                        ).toLocaleString()}</b>
                        <small>Coins</small>
                    </div>

                    <div>
                        ⭐
                        <b>${Number(
                            user.stars || 0
                        ).toLocaleString()}</b>
                        <small>Stars</small>
                    </div>

                    <div>
                        🏆
                        <b>${user.level || 1}</b>
                        <small>Level</small>
                    </div>

                    <div>
                        ⚡
                        <b>${Number(
                            user.xp || 0
                        ).toLocaleString()}</b>
                        <small>XP</small>
                    </div>
                </div>

                <div class="premium-box">
                    ${
                        user.premium_until
                            ? "👑 Premium активно"
                            : "FREE аккаунт"
                    }
                </div>

                <div class="grid">
                    <button
                        class="primary"
                        onclick="showInventory()"
                    >
                        🎒 Инвентарь
                    </button>

                    <button
                        class="primary"
                        onclick="showLeaderboard()"
                    >
                        🏆 Рейтинг
                    </button>
                </div>
            </div>
        `);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// LEADERBOARD
// ============================================================

async function showLeaderboard() {
    try {
        const data = await api("/api/leaderboard");

        openModal(`
            <h2>🏆 Рейтинг</h2>

            ${
                (data.leaderboard || []).map(
                    (user, index) => `
                        <div class="rank-row">
                            <b>#${index + 1}</b>

                            <span>
                                ${escapeHtml(
                                    user.first_name || "Игрок"
                                )}

                                ${
                                    user.username
                                        ? `@${escapeHtml(user.username)}`
                                        : ""
                                }
                            </span>

                            <strong>
                                LVL ${user.level || 1}
                            </strong>

                            <span>
                                ${Number(
                                    user.xp || 0
                                ).toLocaleString()} XP
                            </span>
                        </div>
                    `
                ).join("") ||
                `
                    <p class="muted">
                        Рейтинг пока пуст.
                    </p>
                `
            }
        `);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// BOOSTS
// ============================================================

async function showBoosts() {
    try {
        const data = await api("/api/boosts");

        openModal(`
            <h2>⚡ Мои бусты</h2>

            ${
                (data.boosts || []).map(boost => `
                    <div class="card boost-card">
                        ${img(
                            "",
                            "boost-img",
                            "boost",
                            boost
                        )}

                        <div>
                            <b>
                                ⚡ ${escapeHtml(
                                    boost.type || "BOOST"
                                )}
                            </b>

                            <div class="muted">
                                До:
                                ${
                                    boost.expires_at
                                        ? new Date(
                                            boost.expires_at
                                        ).toLocaleString()
                                        : "—"
                                }
                            </div>
                        </div>
                    </div>
                `).join("") ||
                `
                    <p class="muted">
                        Активных бустов нет.
                    </p>
                `
            }

            <button
                class="primary"
                onclick="showShop()"
            >
                ⭐ ОТКРЫТЬ МАГАЗИН
            </button>
        `);
    } catch (error) {
        toast(error.message);
    }
}

// ============================================================
// DAILY
// ============================================================

async function claimDaily() {
    try {
        const data = await api(
            "/api/daily",
            { method: "POST" }
        );

        toast(
            `🎁 +${
                Number(
                    data.reward || 0
                ).toLocaleString()
            } Coins`
        );

        await loadUser();
    } catch (error) {
        if (error.message === "Награда уже получена") {
            toast("⏳ Сегодня награда уже получена");
        } else {
            toast(error.message);
        }
    }
}

// ============================================================
// NAVIGATION
// ============================================================

function openCases() {
    const section = $("casesSection");
    if (!section) return;

    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

// ============================================================
// TELEGRAM BACK BUTTON
// ============================================================

if (tg) {
    tg.BackButton?.onClick(() => {
        closeModal();
    });
}

// ============================================================
// LOAD
// ============================================================

async function load() {
    if (!checkAuth()) {
        showTelegramRequired();
        return;
    }

    await loadUser();
    await loadCases();
}

// ============================================================
// START
// ============================================================

load();
