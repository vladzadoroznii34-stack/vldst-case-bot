# VLDST CASE — Ultimate

Полный Telegram Bot + Mini App + PostgreSQL.

## В комплекте
- 6 кейсов VLDST CORE / PULSE / AURA / VOID / OVERDRIVE / RIFT
- 49 предметов с редкостями и ценами продажи
- локальные SVG-картинки кейсов и предметов
- Coins
- Telegram Stars: магазин Stars и оплата кейсов через Telegram invoices
- инвентарь и продажа предметов
- профили, уровни, XP
- рефералы
- рейтинг
- задачи
- mini-game
- админ-панель
- бан/разбан
- выдача Coins/Stars
- рассылка рекламы прямо в Telegram
- управление активностью кейсов
- автоматическое создание/обновление базы

## Render
1. Создай PostgreSQL.
2. Создай Web Service из этого проекта.
3. Добавь переменные из `.env.example`.
4. `PUBLIC_URL` = адрес Render.
5. `WEBAPP_URL` = `PUBLIC_URL/webapp/index.html`.
6. `ADMIN_URL` = `PUBLIC_URL/webapp/admin.html`.
7. `BOT_USERNAME` = username бота без @.
8. `BOT_TOKEN` = токен BotFather.
9. `DATABASE_URL` = Internal/External Database URL PostgreSQL, который рекомендует Render для Web Service.

База и все кейсы/предметы создаются автоматически при запуске.

## Важно про Stars
Оплата использует Telegram Bot API invoice с валютой XTR. Telegram Stars пользователя не выдаются "из воздуха": покупатель подтверждает платеж в Telegram, после чего бот начисляет внутренний баланс Stars VLDST или открывает Stars-кейс.

## Локальные картинки
Все изображения находятся в `webapp/assets/`, поэтому отдельные URL-хостинги картинок не нужны.
