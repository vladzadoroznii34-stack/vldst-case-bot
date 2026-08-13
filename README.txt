VLDST CASE FINAL FRONTEND

Файлы:
- index.html — пользовательское Mini App
- admin.html — админ-панель
- app.js — логика Mini App
- admin.js — логика админки
- assets.js — ВСЕ стандартные картинки прямо в коде
- style.css — дизайн

ВАЖНО:
1. assets.js не требует PNG/JPG/WebP/GIF. Все стандартные изображения — SVG data: URL.
2. Если backend возвращает image_url, используется он.
3. Если image_url отсутствует/пустой, автоматически используется встроенная картинка.
4. В admin.html добавлен Telegram WebApp SDK — без него X-Telegram-Init-Data не отправлялся.
5. API-адреса сохранены совместимыми с присланным тобой frontend:
   /api/user
   /api/cases
   /api/cases/<id>/items
   /api/cases/<id>/open
   /api/stars/invoice
   /api/shop
   /api/minigame/play
   /api/referrals
   /api/tasks
   /api/tasks/<id>/claim
   /api/inventory
   /api/inventory/<id>/sell
   /api/leaderboard
   /api/boosts
   /api/daily
   /api/admin/stats
   /api/admin/users
   /api/admin/cases
   /api/admin/give-coins
   /api/admin/give-stars
   /api/admin/user/<id>/premium
   /api/admin/user/<id>/ban
   /api/admin/broadcast
   /api/admin/cases/<id>/toggle

Замечание:
Этот архив — frontend. Для реальной работы нужны твои Flask/aiogram/PostgreSQL endpoints с указанными маршрутами.
