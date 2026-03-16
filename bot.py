#!/usr/bin/env python3
import asyncio
import logging
from config import bot, dp
from handlers import *

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Запуск бота"""
    logging.info("🚀 Бот запускается...")
    
    # Пропускаем накопившиеся обновления
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("⛔ Бот остановлен")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
