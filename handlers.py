import asyncio
from datetime import datetime
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, ChatMemberStatus
from config import bot, dp, DEFAULT_SETTINGS
from database import db
from filters import ModerationFilters

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Приветствие в личке"""
    text = """
🤖 <b>Group Moderator Bot</b>

Я помогу модернировать вашу группу автоматически.

<b>Команды в группе:</b>
/settings - настройки модерации
/stats - статистика
/ban @user - заблокировать
/mute @user - замутить
/warn @user - предупреждение

<b>Добавьте меня в группу</b> и дайте права администратора!
    """
    await message.answer(text)

@dp.message(Command('settings'))
async def cmd_settings(message: types.Message):
    """Просмотр и изменение настроек"""
    chat_id = message.chat.id
    
    # Проверяем, что команда в группе
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    # Получаем настройки
    settings = db.get_settings(chat_id)
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        db.save_settings(chat_id, settings)
    
    # Показываем настройки
    text = "⚙️ <b>Текущие настройки:</b>\n\n"
    text += f"Удалять спам: {'✅' if settings['delete_spam'] else '❌'}\n"
    text += f"Удалять ссылки: {'✅' if settings['delete_links'] else '❌'}\n"
    text += f"Удалять мат: {'✅' if settings['delete_swear'] else '❌'}\n"
    text += f"Приветствие: {'✅' if settings['welcome_enabled'] else '❌'}\n"
    text += f"Капча: {'✅' if settings['captcha_enabled'] else '❌'}\n"
    text += f"Мин. возраст (часы): {settings['min_age_hours']}\n"
    text += f"Мин. фото: {settings['min_photos']}\n"
    
    # Кнопки для изменения (упрощенно)
    await message.answer(text)

@dp.message(Command('stats'))
async def cmd_stats(message: types.Message):
    """Статистика модерации"""
    chat_id = message.chat.id
    
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    stats = db.get_stats(chat_id)
    
    text = "📊 <b>Статистика за 7 дней:</b>\n\n"
    if stats:
        for action, count in stats:
            emoji = {
                'delete': '🗑',
                'ban': '🔨',
                'mute': '🔇',
                'warn': '⚠️'
            }.get(action, '•')
            text += f"{emoji} {action}: {count}\n"
    else:
        text += "Пока нет статистики"
    
    await message.answer(text)

@dp.message(Command('ban'))
async def cmd_ban(message: types.Message):
    """Бан пользователя"""
    # Проверка прав администратора
    # TODO: реализовать
    await message.answer("🔨 Функция бана (будет позже)")

@dp.message(Command('mute'))
async def cmd_mute(message: types.Message):
    """Мут пользователя"""
    await message.answer("🔇 Функция мута (будет позже)")

@dp.message(Command('warn'))
async def cmd_warn(message: types.Message):
    """Предупреждение"""
    await message.answer("⚠️ Функция предупреждений (будет позже)")

@dp.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Новый участник в группе"""
    chat_id = message.chat.id
    settings = db.get_settings(chat_id)
    
    if not settings or not settings.get('welcome_enabled'):
        return
    
    for user in message.new_chat_members:
        # Игнорируем ботов
        if user.is_bot:
            continue
        
        # Приветствие
        welcome_text = settings.get('welcome_text', DEFAULT_SETTINGS['welcome_text'])
        welcome_text = welcome_text.replace('{name}', user.full_name)
        
        await message.answer(welcome_text)
        
        # Капча для новых (опционально)
        if settings.get('captcha_enabled'):
            await send_captcha(message.chat.id, user.id)
        
        db.add_stat(chat_id, 'join')

async def send_captcha(chat_id, user_id):
    """Отправляет капчу пользователю"""
    # TODO: реализовать капчу
    pass

@dp.message(F.left_chat_member)
async def on_user_left(message: types.Message):
    """Участник покинул группу"""
    chat_id = message.chat.id
    db.add_stat(chat_id, 'leave')

@dp.message()
async def moderate_message(message: types.Message):
    """Основная модерация сообщений"""
    # Игнорируем личные сообщения
    if message.chat.type == 'private':
        return
    
    # Игнорируем сообщения от ботов
    if message.from_user.is_bot:
        return
    
    # Получаем настройки группы
    settings = db.get_settings(message.chat.id)
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        db.save_settings(message.chat.id, settings)
    
    # Проверяем сообщение
    filters = ModerationFilters(settings)
    reasons = await filters.check_message(message, bot)
    
    if reasons:
        # Удаляем сообщение
        try:
            await message.delete()
            db.add_stat(message.chat.id, 'delete')
            
            # Логируем нарушителя
            db.add_offender(
                message.chat.id,
                message.from_user.id,
                message.from_user.username,
                ', '.join(reasons)
            )
            
            # Отправляем предупреждение (опционально)
            if len(reasons) > 0:
                warn_text = f"⚠️ {message.from_user.full_name}, ваше сообщение удалено за: {', '.join(reasons)}"
                await message.answer(warn_text, delete_after=5)
                
        except Exception as e:
            print(f"Ошибка удаления: {e}")
