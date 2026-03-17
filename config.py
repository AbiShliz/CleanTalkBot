import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")

LOG_CHANNEL = os.getenv('LOG_CHANNEL')  # ID канала для логов (например -1001234567890)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

DEFAULT_SETTINGS = {
    'delete_spam': True,
    'delete_links': False,
    'delete_swear': True,
    'welcome_enabled': True,
    'welcome_text': '👋 Добро пожаловать, {name}!',
    'captcha_enabled': False,
    'min_age_hours': 24,
    'warn_limit': 3,
    'admin_ids': []
}
