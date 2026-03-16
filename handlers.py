import datetime
import re
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, ChatMember
from aiogram.exceptions import TelegramBadRequest
from config import bot, dp, DEFAULT_SETTINGS
from database import db
from filters import ModerationFilters

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def parse_time_advanced(time_str: str) -> int:
    """
    Преобразует сложные временные строки в секунды.
    Поддерживает: 5, 10m, 2h, 1d, 30s, 3d 12h, 1d 6h 30m
    """
    if not time_str or time_str.lower() == 'inf':
        return -1  # бесконечный мут
    
    total_seconds = 0
    
    # Ищем все комбинации число+единица
    patterns = [
        (r'(\d+)\s*d', 86400),   # дни
        (r'(\d+)\s*h', 3600),    # часы
        (r'(\d+)\s*m', 60),      # минуты
        (r'(\d+)\s*s', 1),       # секунды
        (r'^(\d+)$', 60),        # голое число = минуты
    ]
    
    for pattern, multiplier in patterns:
        matches = re.findall(pattern, time_str.lower())
        for match in matches:
            total_seconds += int(match) * multiplier
    
    return total_seconds if total_seconds > 0 else -1

def format_time_detailed(seconds: int) -> str:
    """Форматирует секунды в человекочитаемый вид (дни, часы, минуты)"""
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

async def is_admin(chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]
    except:
        return False

# ==================== КОМАНДЫ ====================

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Начало работы"""
    text = """
🤖 <b>Антиспам Бот</b>

Я помогаю модернировать группы Telegram автоматически.

<b>Команды в группе:</b>
/settings - настройки модерации
/stats - статистика нарушений
/ban - заблокировать (ответом)
/mute 10 - замутить на 10 минут
/mute 2h - замутить на 2 часа
/mute 1d - замутить на 1 день
/mute 3d 12h - замутить на 3.5 дня
/mute - навсегда
/unmute - снять мут
/warn - выдать предупреждение

<b>Добавьте меня в группу</b> и дайте права администратора!
    """
    await message.answer(text)

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    """Подробная справка"""
    text = """
📚 <b>Полная справка:</b>

<b>Настройки:</b>
/settings - текущие настройки

<b>Модерация (ответом на сообщение):</b>
/ban - навсегда заблокировать
/mute [время] - замутить
   /mute 10       - 10 минут
   /mute 2h       - 2 часа
   /mute 1d       - 1 день
   /mute 30m      - 30 минут
   /mute 3d 12h   - 3 дня 12 часов
   /mute          - навсегда
/unmute - снять мут
/warn - выдать предупреждение

<b>Для владельцев групп:</b>
В разработке:
- Капча для новых
- Белый список
- Свои правила
    """
    await message.answer(text)

@dp.message(Command('settings'))
async def cmd_settings(message: types.Message):
    """Просмотр настроек"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    settings = db.get_settings(message.chat.id)
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        db.save_settings(message.chat.id, settings)
    
    text = "⚙️ <b>Текущие настройки:</b>\n\n"
    text += f"🚫 Удалять спам: {'✅' if settings['delete_spam'] else '❌'}\n"
    text += f"🔗 Удалять ссылки: {'✅' if settings['delete_links'] else '❌'}\n"
    text += f"🤬 Удалять мат: {'✅' if settings['delete_swear'] else '❌'}\n"
    text += f"👋 Приветствие: {'✅' if settings['welcome_enabled'] else '❌'}\n"
    
    await message.answer(text)

@dp.message(Command('stats'))
async def cmd_stats(message: types.Message):
    """Статистика модерации"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    stats = db.get_stats(message.chat.id)
    
    text = "📊 <b>Статистика за 7 дней:</b>\n\n"
    if stats:
        for action, count in stats:
            emoji = {
                'delete': '🗑',
                'join': '👋',
                'leave': '👋',
                'ban': '🔨',
                'mute': '🔇',
                'unmute': '🔊',
                'warn': '⚠️'
            }.get(action, '•')
            text += f"{emoji} {action}: {count}\n"
    else:
        text += "Пока нет статистики"
    
    await message.answer(text)

@dp.message(Command('ban'))
async def cmd_ban(message: types.Message):
    """Бан пользователя"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только администраторы могут использовать эту команду")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя, которого хотите забанить")
        return
    
    user = message.reply_to_message.from_user
    try:
        await message.chat.ban(user.id)
        await message.answer(f"🔨 Пользователь {user.full_name} забанен навсегда")
        db.add_stat(message.chat.id, 'ban')
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command('mute'))
async def cmd_mute(message: types.Message):
    """Умный мут с поддержкой любого времени"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только администраторы могут использовать эту команду")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя, которого хотите замутить")
        return
    
    # Получаем аргументы команды (всё, что после /mute)
    args = message.text.split(maxsplit=1)
    time_str = args[1] if len(args) > 1 else ""
    
    # Парсим время
    mute_seconds = parse_time_advanced(time_str)
    
    user = message.reply_to_message.from_user
    
    try:
        if mute_seconds == -1:
            # Бесконечный мут
            await message.chat.restrict(
                user.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            duration_text = "навсегда"
        else:
            # Мут на определенное время
            until_date = datetime.datetime.now() + datetime.timedelta(seconds=mute_seconds)
            await message.chat.restrict(
                user.id,
                permissions=types.ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            duration_text = f"на {format_time_detailed(mute_seconds)}"
        
        await message.answer(f"🔇 {user.full_name} замучен {duration_text}")
        db.add_stat(message.chat.id, 'mute')
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command('unmute'))
async def cmd_unmute(message: types.Message):
    """Снятие мута"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только администраторы могут использовать эту команду")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя, с которого хотите снять мут")
        return
    
    user = message.reply_to_message.from_user
    
    try:
        await message.chat.restrict(
            user.id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.answer(f"🔊 {user.full_name} снова может писать")
        db.add_stat(message.chat.id, 'unmute')
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command('warn'))
async def cmd_warn(message: types.Message):
    """Предупреждение"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только администраторы могут использовать эту команду")
        return
    
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя, которому хотите выдать предупреждение")
        return
    
    user = message.reply_to_message.from_user
    await message.answer(f"⚠️ {user.full_name}, вы получили предупреждение")
    db.add_stat(message.chat.id, 'warn')

# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

@dp.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Новый участник в группе"""
    chat_id = message.chat.id
    settings = db.get_settings(chat_id)
    
    if not settings or not settings.get('welcome_enabled'):
        return
    
    for user in message.new_chat_members:
        if user.is_bot:
            continue
        
        welcome_text = settings.get('welcome_text', DEFAULT_SETTINGS['welcome_text'])
        welcome_text = welcome_text.replace('{name}', user.full_name)
        
        await message.answer(welcome_text)
        db.add_stat(chat_id, 'join')

@dp.message(F.left_chat_member)
async def on_user_left(message: types.Message):
    """Участник покинул группу"""
    db.add_stat(message.chat.id, 'leave')

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def moderate_message(message: types.Message):
    """Автоматическая модерация сообщений в группах"""
    # Пропускаем сообщения от ботов
    if message.from_user.is_bot:
        return
    
    # Пропускаем админов
    if await is_admin(message.chat.id, message.from_user.id):
        return
    
    # Получаем настройки группы
    settings = db.get_settings(message.chat.id)
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        db.save_settings(message.chat.id, settings)
    
    # Проверяем сообщение
    filters = ModerationFilters(settings)
    reasons = filters.check_message(message.text or "")
    
    if reasons:
        try:
            await message.delete()
            db.add_stat(message.chat.id, 'delete')
            
            # Отправляем уведомление (удалится через 5 секунд)
            warn_text = f"⚠️ {message.from_user.full_name}, ваше сообщение удалено за: {', '.join(reasons)}"
            await message.answer(warn_text, delete_after=5)
        except Exception as e:
            print(f"Ошибка удаления: {e}")
