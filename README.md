# VLDST CASE — исправленная версия

Готовый проект Telegram Mini App + Flask + aiogram 3 + PostgreSQL.

## Что исправлено

- `/`, `/index.html`, `/webapp` и `/webapp/` открывают Mini App без 404.
- `/admin` и `/admin/` открывают админ-панель.
- `/health` добавлен для Render.
- Все frontend-ресурсы лежат в `webapp/`.
- Стандартные картинки встроены в `webapp/assets.js` как SVG data URL — отдельные PNG/JPG добавлять не нужно.
- Картинки кейсов, предметов, Premium, бустов, мини-игры и рефералов генерируются автоматически.
- Telegram Mini App `initData` проверяется на сервере.
- PostgreSQL-схема создаётся автоматически.
- При первом запуске создаются 6 кейсов, 30 предметов и базовые задания.
- Уровень автоматически рассчитывается из XP.
- Бусты x2 Coins / x2 XP реально учитываются.
- Инвентарь, продажа, daily, задания, рейтинг и рефералы работают через API.
- Добавлена интерактивная мини-игра VLDST RUSH: 7 секунд на нажатия.
- Добавлена визуальная анимация открытия кейса.
- Награды кейсов выдаются по фиксированной последовательности, а не случайно, чтобы платная покупка не превращалась в азартный лутбокс.
- Stars используются через Telegram Invoice (`XTR`).
- Проверяются валюта и сумма успешного платежа перед выдачей товара.
- Админ-панель: статистика, поиск пользователей, Coins, внутренние Stars, Premium, бан/разбан, рассылка, включение/выключение кейсов.

## Переменные Render

Создай в Render → Environment:

```text
BOT_TOKEN=токен_бота
DATABASE_URL=строка_подключения_PostgreSQL
WEBAPP_URL=https://твой-сервис.onrender.com
ADMIN_IDS=123456789
BOT_USERNAME=VLDST_CASE_BOT
```

`WEBAPP_URL` должен быть **только базовым адресом**, без `/webapp` и без `/admin`.

Например:

```text
WEBAPP_URL=https://vldst-case-bot.onrender.com
```

## Render

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
python bot.py
```

Health check:

```text
/health
```

## Важно

1. После изменения `BOT_TOKEN`, `DATABASE_URL`, `WEBAPP_URL` или `ADMIN_IDS` сделай новый Deploy.
2. Открывай Mini App кнопкой `/start` в Telegram, а не обычной вкладкой браузера: API использует Telegram `initData`.
3. Админку открывай командой `/admin`.
4. Если база уже была создана старой версией, существующие данные пользователей сохраняются.
5. Не вставляй токен бота в HTML, JavaScript или Git.

## Структура

- `bot.py` — Flask API, aiogram и PostgreSQL.
- `webapp/index.html` — Mini App.
- `webapp/app.js` — логика Mini App.
- `webapp/admin.html` — админка.
- `webapp/admin.js` — логика админки.
- `webapp/assets.js` — встроенные изображения.
- `webapp/style.css` — дизайн.
- `render.yaml` — настройки Render.
