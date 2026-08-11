import os
import asyncio
from threading import Thread

from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

app = Flask(__name__)


@app.route("/")
def home():
    return "VLDST Backend is running!"


def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Открыть VLDST",
                    callback_data="open_vldst"
                )
            ]
        ]
    )

    await message.answer(
        "🌌 <b>VLDST</b>\n\n"
        "Добро пожаловать в VLDST.\n"
        "Скоро здесь появится твоя игровая коллекция.\n\n"
        "🪙 Coins: 0\n"
        "⭐ Stars: 0",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
