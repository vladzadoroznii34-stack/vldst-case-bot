# VLDST CASE — FINAL MOBILE V2

Полностью собранная мобильная версия Telegram Mini App + Telegram-бот + PostgreSQL.

## Что уже внутри
- 6 игровых кейсов VLDST с SVG-артом
- 49 уникальных SVG-предметов и редкости
- открытие кейса за Coins и за настоящие Telegram Stars
- анимация открытия кейса
- списание Coins и выдача предмета в инвентарь
- продажа предметов
- профиль, XP, уровни, Premium и Luck Boost
- реферальная система 500 Coins
- рейтинг Top-100
- задания + награды
- ежедневный бонус
- мини-игра VLDST RUSH с серверной проверкой и cooldown
- промокоды
- Stars Store: Premium, Luck Boost, Coin Packs и внутренний Stars-баланс
- полноценная админ-панель: статистика, пользователи, бан/разбан, Coins, Stars, Premium, Luck, сброс, кейсы, магазин, задания, промокоды
- рекламная рассылка прямо в чат бота + история рассылок
- адаптивный gaming/premium UI для телефона

## Render
Build Command:
`pip install -r requirements.txt`

Start Command:
`python bot.py`

## Environment Variables
Скопируй значения из `.env.example` в Environment Variables Render:

- `BOT_TOKEN` — токен BotFather
- `DATABASE_URL` — Internal Database URL PostgreSQL Render
- `ADMIN_ID` — твой Telegram ID
- `PUBLIC_URL` — адрес Render-сервиса, например `https://vldst-case-bot.onrender.com`
- `WEBAPP_URL` — `https://твой-домен.onrender.com/webapp/index.html`
- `ADMIN_URL` — `https://твой-домен.onrender.com/webapp/admin.html`
- `BOT_USERNAME` — username бота без @

## Telegram Stars
Код использует Telegram invoices с валютой `XTR`. Для покупки пользователь должен открыть Mini App внутри Telegram. После успешной оплаты бот получает `successful_payment` и сразу выполняет товар: Coins / Premium / Luck Boost / открытие кейса.

## Важно
Старую базу удалять не нужно. При запуске `init_database()` создаёт недостающие поля и исправляет старую таблицу `case_items`: удаляет дубли и создаёт уникальный индекс `(case_id,item_id)`, поэтому прежняя ошибка `InvalidColumnReference` не должна повториться.
