import os
import asyncio
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from threading import Thread

import psycopg
from flask import Flask, send_from_directory, request
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден")

WEBAPP_URL = "https://vldst-case-bot.onrender.com/webapp/index.html"

app = Flask(__name__)


@app.route("/")
def home():
    return "VLDST Backend is running!"


@app.route("/webapp/<path:filename>")
def webapp(filename):
    return send_from_directory("webapp", filename)


def verify_telegram_init_data(init_data: str):
    if not init_data:
        return None

    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))

        received_hash = data.pop("hash", None)

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(data.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user_data = data.get("user")

        if not user_data:
            return None

        return json.loads(user_data)

    except Exception:
        return None


@app.route("/api/user")
def get_user():

    init_data = request.headers.get("X-Telegram-Init-Data")

    telegram_user = verify_telegram_init_data(init_data)

    if not telegram_user:
        return {
            "error": "unauthorized"
        }, 401

    telegram_id = telegram_user.get("id")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    coins,
                    stars,
                    level,
                    xp
                FROM users
                WHERE telegram_id = %s
                """,
                (telegram_id,)
            )

            user = cur.fetchone()

    if not user:
        return {
            "error": "user not found"
        }, 404

    return {
        "telegram_id": user[0],
        "username": user[1],
        "first_name": user[2],
        "coins": user[3],
        "stars": user[4],
        "level": user[5],
        "xp": user[6]
    }


def run_web():

    port = int(
        os.getenv("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


def init_database():

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    coins BIGINT NOT NULL DEFAULT 0,
                    stars BIGINT NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    xp BIGINT NOT NULL DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    referred_by BIGINT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

        conn.commit()


def create_or_update_user(
    telegram_id,
    username,
    first_name
):

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            referral_code = (
                f"VLDST{telegram_id}"
            )

            cur.execute(
                """
                INSERT INTO users
                    (
                        telegram_id,
                        username,
                        first_name,
                        referral_code
                    )
                VALUES
                    (%s, %s, %s, %s)

                ON CONFLICT (telegram_id)

                DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name

                RETURNING
                    coins,
                    stars,
                    level,
                    xp;
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    referral_code
                )
            )

            result = cur.fetchone()

        conn.commit()

    return result


bot = Bot(
    token=TOKEN
)

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):

    user = message.from_user

    coins, stars, level, xp = create_or_update_user(
        user.id,
        user.username,
        user.first_name
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Открыть VLDST",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    )
                )
            ]
        ]
    )

    await message.answer(
        f"🌌 <b>VLDST</b>\n\n"
        f"Добро пожаловать, "
        f"<b>{user.first_name}</b>!\n\n"
        f"🪙 Coins: <b>{coins:,}</b>\n"
        f"⭐ Stars: <b>{stars}</b>\n"
        f"⭐ Уровень: <b>{level}</b>\n"
        f"⚡ XP: <b>{xp}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def main():

    init_database()

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":

    Thread(
        target=run_web,
        daemon=True
    ).start()

    asyncio.run(
        main()
            )
