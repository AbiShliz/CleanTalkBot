import os
import socket
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

# Загружаем переменные окружения
load_dotenv()

# Токен бота (из .env файла)
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройки для IPv4 (важно для Sprinthost!)
def create_bot():
    """Создает бота с принудительным IPv4"""
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    session = AiohttpSession(connector=connector)
    return Bot(token=BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)

# Создаем бота и диспетчер
bot = create_bot()
dp = Dispatcher()

# Настройки модерации (можно менять)
DEFAULT_SETTINGS = {
    'delete_spam': True,           # Удалять спам
    'delete_links': False,          # Удалять ссылки
    'delete_swear': True,           # Удалять мат
    'welcome_enabled': True,        # Приветствие новых
    'welcome_text': '👋 Добро пожаловать, {name}!',  # Текст приветствия
    'captcha_enabled': False,        # Капча для новых
    'min_age_hours': 24,            # Минимальный возраст аккаунта (часы)
    'min_photos': 0,                 # Минимум фото в профиле
    'admin_ids': []                  # ID администраторов
}
