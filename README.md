# VLDST CASE — FULL CODE-ASSET EDITION

Полный Telegram Mini App + backend для VLDST CASE.

## Главное отличие этой версии
Все изображения кейсов, предметов, магазина и мини-игры создаются **кодом** как SVG.
В проекте нет PNG/JPG/WebP/SVG-файлов ассетов.

Генератор: `asset-generator.js`

Маршруты:
- `/assets-code/case/:id.svg`
- `/assets-code/item/:id.svg`
- `/assets-code/shop/:code.svg`
- `/assets-code/game.svg`

## Системы
- Telegram Mini App
- 7 кейсов VLDST
- Coins
- предметы #6–#54
- редкости COMMON / RARE / EPIC / LEGENDARY / MYTHIC
- инвентарь
- продажа предметов
- анимация рулетки
- ежедневная награда
- XP и уровни
- задания
- рефералы
- промокоды
- лидерборд
- VLDST REACTOR — мини-игра на реакцию
- Star Shop
- фиксированные покупки за Telegram Stars
- Boost ×2 / ×3 / ×5
- Premium 30 / 90 дней
- косметика профиля
- автоматическая выдача покупки после `successful_payment`
- админ-панель
- управление пользователями
- выдача Coins
- промокоды
- управление товарами Stars
- включение/выключение товаров
- изменение цены Stars
- SQLite
- Render

## Важно про кейсы
Открытие кейсов сделано за внутренние Coins. Stars используются только для фиксированных цифровых товаров Star Shop.

## Переменные окружения Render

`BOT_TOKEN` — токен Telegram-бота.

`ADMIN_KEY` — секрет для `/admin.html`.

`BOT_USERNAME` — username бота без `@`.

`WEBAPP_URL` — URL Render-приложения.

`DEMO_MODE` — для разработки можно оставить `true`; для продакшена рекомендуется `false`.

## Запуск

```bash
npm install
npm start
```

## Webhook Telegram

После деплоя нужно направить webhook Telegram на:

`https://ВАШ-ДОМЕН/telegram/webhook`

Можно сделать через Bot API:

```text
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://ВАШ-ДОМЕН/telegram/webhook
```

## Mini App

В BotFather укажи URL Web App:

`https://ВАШ-ДОМЕН/`

## Админка

Открой:

`https://ВАШ-ДОМЕН/admin.html`

и введи значение `ADMIN_KEY`.

## Безопасность

Не публикуй `BOT_TOKEN` и `ADMIN_KEY` в исходниках или в GitHub.
