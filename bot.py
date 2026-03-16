#!/usr/bin/env python3
import asyncio
import logging
import sys
from config import bot, dp
from handlers import *  # импортируем все обработчики

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Запуск бота"""
    logging.info("Бот запускается...")
    
    # Пропускаем накопившиеся обновления
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Правильный запуск для Python 3.7+
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
