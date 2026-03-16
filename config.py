import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")

# Создаем бота с HTML-разметкой
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Настройки по умолчанию для групп
DEFAULT_SETTINGS = {
    'delete_spam': True,        # удалять спам
    'delete_links': False,       # удалять ссылки
    'delete_swear': True,        # удалять мат
    'welcome_enabled': True,     # приветствие новых
    'welcome_text': '👋 Добро пожаловать, {name}!',
    'captcha_enabled': False,    # капча для новых
    'min_age_hours': 24,         # мин. возраст аккаунта
    'admin_ids': []              # ID админов
}
