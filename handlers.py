from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, ChatMember
from config import bot, dp, DEFAULT_SETTINGS
from database import db
from filters import ModerationFilters

# ==================== КОМАНДЫ ====================

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Начало работы"""
    text = """
🤖 <b>Антиспам Бот</b>

Я помогаю модернировать группы Telegram.

<b>Команды в группе:</b>
/settings - настройки
/stats - статистика
/ban - заблокировать
/mute - замутить
/warn - предупредить

<b>Добавьте меня в группу</b> и дайте права администратора!
    """
    await message.answer(text)

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    """Помощь"""
    text = """
📚 <b>Справка по командам:</b>

<b>/settings</b> - просмотр и изменение настроек
<b>/stats</b> - статистика модерации
<b>/ban</b> @user - заблокировать
<b>/mute</b> @user - замутить
<b>/warn</b> @user - предупредить

В разработке:
- Капча для новых
- Фильтр спама
- Белый список
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
    text += f"Удалять спам: {'✅' if settings['delete_spam'] else '❌'}\n"
    text += f"Удалять ссылки: {'✅' if settings['delete_links'] else '❌'}\n"
    text += f"Удалять мат: {'✅' if settings['delete_swear'] else '❌'}\n"
    text += f"Приветствие: {'✅' if settings['welcome_enabled'] else '❌'}\n"
    
    await message.answer(text)

@dp.message(Command('stats'))
async def cmd_stats(message: types.Message):
    """Статистика"""
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в группах")
        return
    
    await message.answer("📊 Статистика пока в разработке")

@dp.message(Command('ban'))
async def cmd_ban(message: types.Message):
    """Бан пользователя"""
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя, которого хотите забанить")
        return
    
    user = message.reply_to_message.from_user
    await message.chat.ban(user.id)
    await message.answer(f"🔨 Пользователь {user.full_name} забанен")

@dp.message(Command('mute'))
async def cmd_mute(message: types.Message):
    """Мут пользователя"""
    await message.answer("🔇 Функция мута в разработке")

@dp.message(Command('warn'))
async def cmd_warn(message: types.Message):
    """Предупреждение"""
    await message.answer("⚠️ Функция предупреждений в разработке")

# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

@dp.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Новый участник"""
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
    """Участник покинул"""
    db.add_stat(message.chat.id, 'leave')

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def moderate_message(message: types.Message):
    """Модерация сообщений в группах"""
    if message.from_user.is_bot:
        return
    
    settings = db.get_settings(message.chat.id)
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        db.save_settings(message.chat.id, settings)
    
    filters = ModerationFilters(settings)
    reasons = filters.check_message(message.text)
    
    if reasons:
        try:
            await message.delete()
            db.add_stat(message.chat.id, 'delete')
            
            warn_text = f"⚠️ {message.from_user.full_name}, ваше сообщение удалено за: {', '.join(reasons)}"
            await message.answer(warn_text, delete_after=5)
        except Exception as e:
            print(f"Ошибка удаления: {e}")
