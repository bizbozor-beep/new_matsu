import asyncio
import os
import threading
from django.apps import AppConfig

class LampConfig(AppConfig):
    name = "lamp"

    def ready(self):
        # Faqat runserver paytida bir marta ishga tushishi uchun
        if os.environ.get('RUN_MAIN') == 'true':
            def run_bot_thread():
                from lamp.management.commands.runbot import main_bot
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    print("Telegram bot (aiogram 3.x) avtomatik ishga tushdi...")
                    loop.run_until_complete(main_bot())
                except Exception as e:
                    print(f"Bot xatoligi: {e}")

            thread = threading.Thread(target=run_bot_thread, daemon=True)
            thread.start()
