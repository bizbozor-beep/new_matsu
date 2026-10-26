import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from django.core.management.base import BaseCommand

TOKEN = "8970077275:AAH1AVCjxSvm9t7Md0osBjdHDYjsiP3Rk9k"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start", "help"))
async def cmd_start(message: Message):
    await message.answer("Salom!")

@dp.message(F.text)
async def echo_message(message: Message):
    await message.answer("Salom!")

async def main_bot():
    await dp.start_polling(bot)

class Command(BaseCommand):
    help = 'Telegram botni aiogram 3.x orqali ishga tushiradi'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Telegram bot (aiogram 3.x) ishga tushdi..."))
        asyncio.run(main_bot())
