# VLDST CASE FINAL MOBILE

Замена текущего проекта без уменьшения основных систем. Добавлены мобильный premium/gaming UI, SVG-картинки 6 кейсов и 49 предметов, Stars-магазин с Premium/Boosts, мини-игра и расширенная админка. Важное исправление БД: старая таблица case_items теперь очищает дубликаты и получает уникальный индекс, поэтому ошибка ON CONFLICT(case_id,item_id) устраняется автоматически.

Render: Build Command `pip install -r requirements.txt`; Start Command `python bot.py`. Переменные окружения оставь свои.
