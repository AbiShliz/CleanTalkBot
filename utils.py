import re
import datetime
import random
import string
from config import bot, LOG_CHANNEL
from aiogram.types import ChatMember

def parse_time_advanced(time_str: str) -> int:
    if not time_str or time_str.lower() == 'inf':
        return -1

    total_seconds = 0
    patterns = [
        (r'(\d+)\s*d', 86400),
        (r'(\d+)\s*h', 3600),
        (r'(\d+)\s*m', 60),
        (r'(\d+)\s*s', 1),
        (r'^(\d+)$', 60),
    ]

    for pattern, multiplier in patterns:
        matches = re.findall(pattern, time_str.lower())
        for match in matches:
            total_seconds += int(match) * multiplier

    return total_seconds if total_seconds > 0 else -1

def format_time_detailed(seconds: int) -> str:
    if seconds <= 0:
        return "навсегда"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days} дн")
    if hours > 0:
        parts.append(f"{hours} ч")
    if minutes > 0:
        parts.append(f"{minutes} мин")
    if secs > 0 and not (days or hours or minutes):
        parts.append(f"{secs} сек")

    return " ".join(parts) if parts else "несколько секунд"

def generate_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]
    except:
        return False

async def log_action(chat_id, action, user, admin=None, reason=""):
    if not LOG_CHANNEL:
        return
    try:
        text = f"📋 <b>Действие:</b> {action}\n"
        text += f"👤 <b>Пользователь:</b> {user.full_name} (@{user.username})\n"
        text += f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        text += f"💬 <b>Чат:</b> {chat_id}\n"
        if admin:
            text += f"👮 <b>Админ:</b> {admin.full_name}\n"
        if reason:
            text += f"📝 <b>Причина:</b> {reason}\n"
        await bot.send_message(LOG_CHANNEL, text, parse_mode='HTML')
    except:
        pass