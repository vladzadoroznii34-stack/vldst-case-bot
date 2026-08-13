// ============================================================
// VLDST CASE
// MOBILE WEBAPP
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

const $ = (id) =>
    document.getElementById(id);


const ASSET_FALLBACK =
    "/webapp/assets/fallback.svg";


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

        "Content-Type":
            "application/json",

        "X-Telegram-Init-Data":
            telegramInitData(),

        ...extra

    };

}


// ============================================================
// API
// ============================================================

async function api(
    url,
    options = {}
) {

    const config = {

        ...options,

        headers: authHeaders(
            options.headers || {}
        )

    };


    const response =
        await fetch(
            url,
            config
        );


    let data = {};

    try {

        data =
            await response.json();

    } catch {

        data = {};

    }


    if (!response.ok) {

        if (
            response.status === 401 ||
            data.error === "unauthorized"
        ) {

            throw new Error(
                "Открой VLDST CASE через Telegram"
            );

        }


        if (
            response.status === 403
        ) {

            if (
                data.error === "banned"
            ) {

                throw new Error(
                    "Ваш аккаунт заблокирован"
                );

            }

            throw new Error(
                "Доступ запрещён"
            );

        }


        const messages = {

            not_enough_coins:
                "Недостаточно Coins",

            case_not_found:
                "Кейс не найден",

            case_has_no_items:
                "В кейсе нет предметов",

            already_claimed:
                "Награда уже получена",

            task_not_found:
                "Задание не найдено",

            user_not_found:
                "Пользователь не найден"

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
// IMAGE
// ============================================================

function img(
    src,
    cls = ""
) {

    const safe =
        src &&
        String(src).trim()
            ? src
            : ASSET_FALLBACK;


    return `
        <img
            class="${cls}"
            src="${escapeAttribute(safe)}"
            loading="lazy"
            onerror="
                this.onerror=null;
                this.src='${ASSET_FALLBACK}'
            "
        >
    `;

}


// ============================================================
// TOAST
// ============================================================

function toast(text) {

    const element =
        $("toast");

    if (!element) return;


    element.textContent =
        text;

    element.classList.add(
        "show"
    );


    clearTimeout(
        window.__toastTimer
    );


    window.__toastTimer =
        setTimeout(() => {

            element.classList.remove(
                "show"
            );

        }, 2500);

}


// ============================================================
// MODAL
// ============================================================

function openModal(content) {

    const modal =
        $("modal");

    const sheet =
        $("sheet");


    if (!modal || !sheet)
        return;


    sheet.innerHTML =
        content;


    modal.classList.add(
        "open"
    );


    if (tg?.BackButton) {

        tg.BackButton.show();

    }

}


function closeModal() {

    $("modal")
        ?.classList.remove(
            "open"
        );


    tg?.BackButton?.hide();

}


$("modal")?.addEventListener(
    "click",
    event => {

        if (
            event.target.id === "modal"
        ) {

            closeModal();

        }

    }
);


// ============================================================
// AUTH
// ============================================================

function checkAuth() {

    if (!tg) {

        return false;

    }


    if (!tg.initData) {

        return false;

    }


    return true;

}


// ============================================================
// USER
// ============================================================

async function loadUser() {

    try {

        const user =
            await api(
                "/api/user"
            );


        if (!user)
            return;


        if (user.banned) {

            openModal(`

                <div class="result">

                    <div class="game-icon">
                        ⛔
                    </div>

                    <h2>
                        АККАУНТ ЗАБЛОКИРОВАН
                    </h2>

                    <p class="muted">
                        Доступ к VLDST CASE ограничен.
                    </p>

                </div>

            `);

            return;

        }


        if ($("balance")) {

            $("balance").textContent =
                `🪙 ${Number(
                    user.coins || 0
                ).toLocaleString()} ` +
                `⭐ ${Number(
                    user.stars || 0
                ).toLocaleString()}`;

        }


        if ($("name")) {

            $("name").textContent =
                user.first_name ||
                "Игрок";

        }


        if ($("level")) {

            $("level").textContent =
                `Уровень ${
                    user.level || 1
                } • ${
                    Number(
                        user.xp || 0
                    ).toLocaleString()
                } XP`;

        }


        if ($("xpbar")) {

            const xp =
                Number(
                    user.xp || 0
                );

            $("xpbar").style.width =
                `${xp % 100}%`;

        }


        if ($("premium")) {

            $("premium").textContent =
                user.premium_until
                    ? "👑 PREMIUM"
                    : "FREE";

        }


        return user;

    } catch (error) {

        console.error(error);

        toast(
            error.message
        );

    }

}


// ============================================================
// CASES
// ============================================================

async function loadCases() {

    try {

        const data =
            await api(
                "/api/cases"
            );


        const container =
            $("cases");


        if (!container)
            return;


        const cases =
            data.cases || [];


        container.innerHTML =
            cases.map(
                item => `

                <div class="card case-card">

                    <button
                        class="case-open"
                        onclick="caseInfo(${item.id})"
                    >

                        ${img(
                            item.image_url,
                            "case-img"
                        )}

                        <div class="case-body">

                            <b>
                                ${escapeHtml(
                                    item.name
                                )}
                            </b>

                            <div class="case-price">

                                <span class="price">
                                    🪙 ${
                                        Number(
                                            item.price_coins || 0
                                        ).toLocaleString()
                                    }
                                </span>

                                <span class="pill">
                                    ОТКРЫТЬ
                                </span>

                            </div>

                        </div>

                    </button>

                </div>

            `
            ).join("");


        await loadItems(
            cases
        );


    } catch (error) {

        console.error(error);

        toast(
            "Не удалось загрузить кейсы"
        );

    }

}


// ============================================================
// ITEMS
// ============================================================

async function loadItems(
    cases
) {

    try {

        const allItems = [];


        for (
            const currentCase
            of cases
        ) {

            try {

                const data =
                    await api(
                        `/api/cases/${currentCase.id}/items`
                    );


                if (
                    Array.isArray(
                        data.items
                    )
                ) {

                    allItems.push(
                        ...data.items
                    );

                }

            } catch (
                error
            ) {

                console.warn(
                    error
                );

            }

        }


        const unique = [];

        const ids =
            new Set();


        for (
            const item
            of allItems
        ) {

            if (
                !ids.has(
                    item.id
                )
            ) {

                ids.add(
                    item.id
                );

                unique.push(
                    item
                );

            }

        }


        const container =
            $("items");


        if (!container)
            return;


        container.innerHTML =
            unique
                .slice(0, 49)
                .map(
                    item => `

                    <div
                        class="item ${
                            String(
                                item.rarity ||
                                "common"
                            ).toLowerCase()
                        }"
                    >

                        ${img(
                            item.image_url
                        )}

                        <span>
                            ${escapeHtml(
                                item.name
                            )}
                        </span>

                    </div>

                `
                )
                .join("");


    } catch (
        error
    ) {

        console.error(
            error
        );

    }

}


// ============================================================
// CASE INFO
// ============================================================

async function caseInfo(
    id
) {

    try {

        const cases =
            await api(
                "/api/cases"
            );


        const current =
            cases.cases.find(
                item =>
                    Number(item.id) ===
                    Number(id)
            );


        if (!current) {

            toast(
                "Кейс не найден"
            );

            return;

        }


        const data =
            await api(
                `/api/cases/${id}/items`
            );


        openModal(`

            <div class="case-modal-head">

                ${img(
                    current.image_url,
                    "modal-case-img"
                )}

                <div>

                    <h2>
                        ${escapeHtml(
                            current.name
                        )}
                    </h2>

                    <p class="muted">
                        ${escapeHtml(
                            current.description ||
                            "Эксклюзивный кейс VLDST CASE"
                        )}
                    </p>

                </div>

            </div>


            <div class="grid">

                <button
                    class="primary"
                    onclick="openCase(${id})"
                >
                    🪙 ${
                        Number(
                            current.price_coins || 0
                        ).toLocaleString()
                    }
                </button>


                <button
                    class="primary stars-btn"
                    onclick="buyCase(${id})"
                >
                    ⭐ ${
                        Number(
                            current.price_stars || 0
                        )
                    }
                </button>

            </div>


            <h3>
                🎁 Содержимое
            </h3>


            <div class="item-grid">

                ${(data.items || [])
                    .map(
                        item => `

                        <div
                            class="item ${
                                String(
                                    item.rarity ||
                                    "common"
                                ).toLowerCase()
                            }"
                        >

                            ${img(
                                item.image_url
                            )}

                            <span>
                                ${escapeHtml(
                                    item.name
                                )}
                            </span>

                        </div>

                    `
                    )
                    .join("")}

            </div>

        `);

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// OPEN CASE
// ============================================================

async function openCase(
    id
) {

    try {

        closeModal();

        toast(
            "🎁 Открываем кейс..."
        );


        const data =
            await api(
                `/api/cases/${id}/open`,
                {
                    method: "POST"
                }
            );


        if (!data.item) {

            toast(
                "Не удалось получить предмет"
            );

            return;

        }


        openModal(`

            <div class="result win">

                <div class="win-ring">
                    🎉
                </div>

                <h2>
                    ВЫИГРЫШ!
                </h2>

                ${img(
                    data.item.image_url,
                    "result-img"
                )}

                <h2>
                    ${escapeHtml(
                        data.item.name
                    )}
                </h2>

                <p
                    class="rarity-${String(
                        data.item.rarity ||
                        "common"
                    ).toLowerCase()}"
                >
                    ${escapeHtml(
                        data.item.rarity ||
                        "COMMON"
                    )}
                </p>

                <p class="muted">
                    Продажа:
                    🪙 ${
                        Number(
                            data.item.sell_price || 0
                        ).toLocaleString()
                    }
                </p>

                <button
                    class="primary"
                    onclick="closeModal();load()"
                >
                    ЗАБРАТЬ
                </button>

            </div>

        `);


        await loadUser();

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// BUY CASE STARS
// ============================================================

async function buyCase(
    id
) {

    try {

        const data =
            await api(
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

            toast(
                "Не удалось создать оплату"
            );

            return;

        }


        openInvoice(
            data.invoice_url
        );

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// OPEN TELEGRAM INVOICE
// ============================================================

function openInvoice(
    invoiceUrl
) {

    if (
        tg &&
        typeof tg.openInvoice ===
        "function"
    ) {

        tg.openInvoice(
            invoiceUrl,
            status => {

                console.log(
                    "Payment:",
                    status
                );


                if (
                    status === "paid"
                ) {

                    toast(
                        "⭐ Оплата успешна!"
                    );

                    setTimeout(
                        load,
                        800
                    );

                }

            }
        );

    } else {

        window.open(
            invoiceUrl,
            "_blank"
        );

    }

}


// ============================================================
// SHOP
// ============================================================

async function showShop() {

    openModal(`

        <h2>
            ⭐ Магазин VLDST
        </h2>

        <p class="muted">
            Telegram Stars • Premium • бусты
        </p>

        <div id="shoplist">
            Загрузка...
        </div>

    `);


    try {

        const data =
            await api(
                "/api/shop"
            );


        const container =
            $("shoplist");


        if (!container)
            return;


        const balanceProducts =
            data.balance_products || [];


        const storeProducts =
            data.store_products || [];


        container.innerHTML = `

            <h3>
                ⭐ Пополнение баланса
            </h3>

            ${
                balanceProducts
                    .map(
                        product => `

                        <div class="card shop-row">

                            <div>

                                <b>
                                    ${escapeHtml(
                                        product.title
                                    )}
                                </b>

                                <div class="muted">
                                    Stars на баланс VLDST
                                </div>

                            </div>

                            <button
                                class="primary small"
                                onclick="buyProduct(
                                    '${escapeAttribute(
                                        product.id
                                    )}',
                                    'balance'
                                )"
                            >
                                ⭐ ${
                                    Number(
                                        product.stars
                                    )
                                }
                            </button>

                        </div>

                    `
                    )
                    .join("")
            }


            <h3>
                👑 Premium
            </h3>

            ${
                storeProducts
                    .filter(
                        p =>
                            p.type ===
                            "premium"
                    )
                    .map(
                        product => `

                        <div class="card shop-row">

                            <div>

                                <b>
                                    👑 ${escapeHtml(
                                        product.title
                                    )}
                                </b>

                                <div class="muted">
                                    ${escapeHtml(
                                        product.description
                                    )}
                                </div>

                            </div>

                            <button
                                class="primary small"
                                onclick="buyProduct(
                                    '${escapeAttribute(
                                        product.id
                                    )}',
                                    'store'
                                )"
                            >
                                ⭐ ${
                                    product.stars
                                }
                            </button>

                        </div>

                    `
                    )
                    .join("")
            }


            <h3>
                ⚡ Бусты
            </h3>

            ${
                storeProducts
                    .filter(
                        p =>
                            p.type !==
                            "premium"
                    )
                    .map(
                        product => `

                        <div class="card shop-row">

                            <div>

                                <b>
                                    ⚡ ${escapeHtml(
                                        product.title
                                    )}
                                </b>

                                <div class="muted">
                                    ${escapeHtml(
                                        product.description
                                    )}
                                </div>

                            </div>

                            <button
                                class="primary small"
                                onclick="buyProduct(
                                    '${escapeAttribute(
                                        product.id
                                    )}',
                                    'store'
                                )"
                            >
                                ⭐ ${
                                    product.stars
                                }
                            </button>

                        </div>

                    `
                    )
                    .join("")
            }

        `;

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// PRODUCT
// ============================================================

async function buyProduct(
    id,
    kind
) {

    try {

        const data =
            await api(
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

            toast(
                "Ссылка оплаты не создана"
            );

            return;

        }


        openInvoice(
            data.invoice_url
        );

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// MINI GAME
// ============================================================

async function showMini() {

    openModal(`

        <div class="result">

            <div class="game-icon">
                🎮
            </div>

            <h2>
                VLDST RUSH
            </h2>

            <p class="muted">
                Играй и получай Coins.
            </p>

            <button
                class="primary"
                onclick="play()"
            >
                ⚡ ИГРАТЬ
            </button>

            <div id="game"></div>

        </div>

    `);

}


async function play() {

    try {

        const data =
            await api(
                "/api/minigame/play",
                {
                    method: "POST"
                }
            );


        const game =
            $("game");


        if (game) {

            game.innerHTML = `

                <div class="game-result">

                    <b>
                        Счёт:
                        ${Number(
                            data.score || 0
                        )}
                    </b>

                    <strong>
                        +${
                            Number(
                                data.reward || 0
                            ).toLocaleString()
                        } 🪙
                    </strong>

                </div>

            `;

        }


        await loadUser();

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// REFERRALS
// ============================================================

async function showRef() {

    try {

        const data =
            await api(
                "/api/referrals"
            );


        openModal(`

            <div class="result">

                <div class="game-icon">
                    👥
                </div>

                <h2>
                    РЕФЕРАЛЫ
                </h2>

                <p>
                    Приглашено:
                    <b>
                        ${
                            Number(
                                data.count || 0
                            )
                        }
                    </b>
                </p>

                <p>
                    Заработано:
                    <b>
                        ${
                            Number(
                                data.earned || 0
                            ).toLocaleString()
                        }
                        🪙
                    </b>
                </p>

                <p class="muted">
                    За нового игрока —
                    500 Coins.
                </p>

                <input
                    id="refLink"
                    value="${escapeAttribute(
                        data.referral_link || ""
                    )}"
                    readonly
                >

                <button
                    class="primary"
                    onclick="copyReferral()"
                >
                    🔗 КОПИРОВАТЬ
                </button>

                <button
                    class="primary"
                    onclick="shareReferral()"
                >
                    📤 ПРИГЛАСИТЬ
                </button>

            </div>

        `);

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


async function copyReferral() {

    const input =
        $("refLink");


    if (!input)
        return;


    try {

        await navigator.clipboard.writeText(
            input.value
        );

        toast(
            "Ссылка скопирована"
        );

    } catch {

        input.select();

        document.execCommand(
            "copy"
        );

        toast(
            "Ссылка скопирована"
        );

    }

}


function shareReferral() {

    const input =
        $("refLink");


    if (!input)
        return;


    const text =
        encodeURIComponent(
            "🎁 Заходи в VLDST CASE и получай Coins!"
        );


    const url =
        encodeURIComponent(
            input.value
        );


    if (
        tg?.openTelegramLink
    ) {

        tg.openTelegramLink(
            `https://t.me/share/url?url=${url}&text=${text}`
        );

    } else {

        window.open(
            `https://t.me/share/url?url=${url}&text=${text}`,
            "_blank"
        );

    }

}


// ============================================================
// TASKS
// ============================================================

async function showTasks() {

    try {

        const data =
            await api(
                "/api/tasks"
            );


        openModal(`

            <h2>
                🎯 Задания
            </h2>

            ${
                (data.tasks || [])
                    .map(
                        task => `

                        <div class="card task-row">

                            <div>

                                <b>
                                    ${escapeHtml(
                                        task.title
                                    )}
                                </b>

                                <p class="muted">
                                    ${escapeHtml(
                                        task.description || ""
                                    )}
                                </p>

                                <span class="price">

                                    🪙 ${
                                        Number(
                                            task.reward_coins || 0
                                        ).toLocaleString()
                                    }

                                    ${
                                        task.reward_stars
                                            ? `⭐ ${task.reward_stars}`
                                            : ""
                                    }

                                </span>

                            </div>

                            <button
                                class="primary small"
                                onclick="claim(
                                    ${task.id}
                                )"
                                ${
                                    task.claimed
                                        ? "disabled"
                                        : ""
                                }
                            >
                                ${
                                    task.claimed
                                        ? "✓"
                                        : "ЗАБРАТЬ"
                                }
                            </button>

                        </div>

                    `
                    )
                    .join("")
                ||
                `
                    <p class="muted">
                        Новых заданий нет.
                    </p>
                `
            }

        `);

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


async function claim(
    id
) {

    try {

        await api(
            `/api/tasks/${id}/claim`,
            {
                method: "POST"
            }
        );


        toast(
            "🎁 Награда получена!"
        );


        await loadUser();

        await showTasks();

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// INVENTORY
// ============================================================

async function showInventory() {

    try {

        const data =
            await api(
                "/api/inventory"
            );


        openModal(`

            <h2>
                🎒 Инвентарь
            </h2>

            <p class="muted">
                Полученные предметы
            </p>

            <div class="item-grid">

                ${
                    (data.inventory || [])
                        .map(
                            item => `

                            <div
                                class="item ${
                                    String(
                                        item.rarity ||
                                        "common"
                                    ).toLowerCase()
                                }"
                            >

                                ${img(
                                    item.image_url
                                )}

                                <span>

                                    ${escapeHtml(
                                        item.name
                                    )}

                                    <br>

                                    <button
                                        class="pill"
                                        onclick="sell(
                                            ${item.inventory_id}
                                        )"
                                    >
                                        🪙 ${
                                            Number(
                                                item.sell_price || 0
                                            ).toLocaleString()
                                        }
                                        ПРОДАТЬ
                                    </button>

                                </span>

                            </div>

                        `
                        )
                        .join("")
                    ||
                    `
                        <p class="muted">
                            Инвентарь пуст.
                        </p>
                    `
                }

            </div>

        `);

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// SELL
// ============================================================

async function sell(
    id
) {

    try {

        const data =
            await api(
                `/api/inventory/${id}/sell`,
                {
                    method: "POST"
                }
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

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// PROFILE
// ============================================================

async function showProfile() {

    try {

        const user =
            await api(
                "/api/user"
            );


        openModal(`

            <div class="profile-modal">

                <div class="avatar big">
                    V
                </div>

                <h2>
                    ${escapeHtml(
                        user.first_name ||
                        "Игрок"
                    )}
                </h2>

                <p class="muted">

                    ${
                        user.username
                            ? `@${escapeHtml(
                                user.username
                            )}`
                            : "@player"
                    }

                    • ID
                    ${user.telegram_id}

                </p>


                <div class="profile-stats">

                    <div>

                        🪙

                        <b>
                            ${
                                Number(
                                    user.coins || 0
                                ).toLocaleString()
                            }
                        </b>

                        <small>
                            Coins
                        </small>

                    </div>


                    <div>

                        ⭐

                        <b>
                            ${
                                Number(
                                    user.stars || 0
                                ).toLocaleString()
                            }
                        </b>

                        <small>
                            Stars
                        </small>

                    </div>


                    <div>

                        🏆

                        <b>
                            ${
                                user.level || 1
                            }
                        </b>

                        <small>
                            Level
                        </small>

                    </div>


                    <div>

                        ⚡

                        <b>
                            ${
                                Number(
                                    user.xp || 0
                                ).toLocaleString()
                            }
                        </b>

                        <small>
                            XP
                        </small>

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

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// LEADERBOARD
// ============================================================

async function showLeaderboard() {

    try {

        const data =
            await api(
                "/api/leaderboard"
            );


        openModal(`

            <h2>
                🏆 Рейтинг
            </h2>

            ${
                (data.leaderboard || [])
                    .map(
                        (user, index) => `

                        <div class="rank-row">

                            <b>
                                #${index + 1}
                            </b>

                            <span>

                                ${escapeHtml(
                                    user.first_name ||
                                    "Игрок"
                                )}

                                ${
                                    user.username
                                        ? `@${escapeHtml(
                                            user.username
                                        )}`
                                        : ""
                                }

                            </span>

                            <strong>
                                LVL ${
                                    user.level || 1
                                }
                            </strong>

                            <span>
                                ${
                                    Number(
                                        user.xp || 0
                                    ).toLocaleString()
                                }
                                XP
                            </span>

                        </div>

                    `
                    )
                    .join("")
                ||
                `
                    <p class="muted">
                        Рейтинг пока пуст.
                    </p>
                `
            }

        `);

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// BOOSTS
// ============================================================

async function showBoosts() {

    try {

        const data =
            await api(
                "/api/boosts"
            );


        openModal(`

            <h2>
                ⚡ Мои бусты
            </h2>

            ${
                (data.boosts || [])
                    .map(
                        boost => `

                        <div class="card">

                            <b>
                                ⚡ ${escapeHtml(
                                    boost.type ||
                                    "BOOST"
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

                    `
                    )
                    .join("")
                ||
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

    } catch (
        error
    ) {

        toast(
            error.message
        );

    }

}


// ============================================================
// DAILY
// ============================================================

async function claimDaily() {

    try {

        const data =
            await api(
                "/api/daily",
                {
                    method: "POST"
                }
            );


        toast(
            `🎁 +${
                Number(
                    data.reward || 0
                ).toLocaleString()
            } Coins`
        );


        await loadUser();

    } catch (
        error
    ) {

        if (
            error.message ===
            "Награда уже получена"
        ) {

            toast(
                "⏳ Сегодня награда уже получена"
            );

        } else {

            toast(
                error.message
            );

        }

    }

}


// ============================================================
// NAVIGATION
// ============================================================

function openCases() {

    const section =
        $("casesSection");


    if (!section)
        return;


    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// ============================================================
// TELEGRAM BACK BUTTON
// ============================================================

if (tg) {

    tg.BackButton?.onClick(
        () => {

            closeModal();

        }
    );

}


// ============================================================
// REQUIRED
// ============================================================

function showTelegramRequired() {

    openModal(`

        <div class="result">

            <div class="game-icon">
                📱
            </div>

            <h2>
                VLDST CASE
            </h2>

            <p class="muted">
                Приложение необходимо открыть
                через Telegram.
            </p>

            <button
                class="primary"
                onclick="closeModal()"
            >
                ПОНЯТНО
            </button>

        </div>

    `);

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
