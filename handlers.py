import datetime
from aiogram import types, F
from aiogram.filters import Command
from config import bot, dp, DEFAULT_SETTINGS, LOG_CHANNEL
from database import db
from filters import ModerationFilters
from utils import (
    parse_time_advanced, format_time_detailed,
    generate_captcha, is_admin, log_action
)

# ==================== КОМАНДЫ ====================

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    text = """
🤖 <b>Антиспам Бот v2.0</b>

Я помогаю модернировать группы Telegram автоматически.

<b>Команды в группе:</b>
/settings - настройки
/stats - статистика
/ban - заблокировать (ответом)
/mute [время] - замутить (10, 2h, 1d)
/unmute - снять мут
/warn [причина] - предупреждение
/warns - показать предупреждения
/whitelist_add - добавить в белый список
/whitelist_remove - удалить из белого списка
/captcha on/off - включить/выключить капчу
/toggle [spam/links/swear] - вкл/выкл функции
/set_welcome [текст] - установить приветствие
/set_warnlimit [число] - лимит предупреждений

<b>Добавьте меня в группу</b> и дайте права администратора!
    """
    await message.answer(text)

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    await cmd_start(message)

@dp.message(Command('settings'))
async def cmd_settings(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("❌ Эта команда работает только в группах")
        return

    settings = db.get_settings(message.chat.id) or DEFAULT_SETTINGS.copy()
    text = "⚙️ <b>Текущие настройки:</b>\n\n"
    text += f"🚫 Спам: {'✅' if settings['delete_spam'] else '❌'}\n"
    text += f"🔗 Ссылки: {'✅' if settings['delete_links'] else '❌'}\n"
    text += f"🤬 Мат: {'✅' if settings['delete_swear'] else '❌'}\n"
    text += f"👋 Приветствие: {'✅' if settings['welcome_enabled'] else '❌'}\n"
    text += f"🔐 Капча: {'✅' if settings['captcha_enabled'] else '❌'}\n"
    text += f"⚠️ Лимит варнов: {settings.get('warn_limit', 3)}\n"
    await message.answer(text)

@dp.message(Command('stats'))
async def cmd_stats(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("❌ Только в группах")
        return
    stats = db.get_stats(message.chat.id)
    text = "📊 <b>Статистика за 7 дней:</b>\n\n"
    if stats:
        for action, count in stats:
            text += f"• {action}: {count}\n"
    else:
        text += "Нет данных"
    await message.answer(text)

@dp.message(Command('ban'))
async def cmd_ban(message: types.Message):
    if message.chat.type == 'private':
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только админы")
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return

    user = message.reply_to_message.from_user
    try:
        await message.chat.ban(user.id)
        await message.answer(f"🔨 {user.full_name} забанен")
        await log_action(message.chat.id, "Бан", user, message.from_user)
        db.add_stat(message.chat.id, 'ban')
    except Exception as e:
        await message.answer(f"❌ {e}")

@dp.message(Command('mute'))
async def cmd_mute(message: types.Message):
    if message.chat.type == 'private':
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только админы")
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return

    args = message.text.split(maxsplit=1)
    time_str = args[1] if len(args) > 1 else ""
    mute_seconds = parse_time_advanced(time_str)
    user = message.reply_to_message.from_user

    try:
        if mute_seconds == -1:
            await message.chat.restrict(
                user.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            duration_text = "навсегда"
        else:
            until_date = datetime.datetime.now() + datetime.timedelta(seconds=mute_seconds)
            await message.chat.restrict(
                user.id,
                permissions=types.ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            duration_text = f"на {format_time_detailed(mute_seconds)}"

        await message.answer(f"🔇 {user.full_name} замучен {duration_text}")
        await log_action(message.chat.id, f"Мут {duration_text}", user, message.from_user, time_str)
        db.add_stat(message.chat.id, 'mute')
    except Exception as e:
        await message.answer(f"❌ {e}")

@dp.message(Command('unmute'))
async def cmd_unmute(message: types.Message):
    if message.chat.type == 'private':
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только админы")
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
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
        await message.answer(f"🔊 {user.full_name} размучен")
        await log_action(message.chat.id, "Размут", user, message.from_user)
        db.add_stat(message.chat.id, 'unmute')
    except Exception as e:
        await message.answer(f"❌ {e}")

@dp.message(Command('warn'))
async def cmd_warn(message: types.Message):
    if message.chat.type == 'private':
        return
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("⛔ Только админы")
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return

    user = message.reply_to_message.from_user
    args = message.text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else "без причины"
    settings = db.get_settings(message.chat.id) or DEFAULT_SETTINGS
    warn_limit = settings.get('warn_limit', 3)

    count = db.add_warn(message.chat.id, user.id, user.full_name, reason)

    if count >= warn_limit:
        try:
            await message.chat.ban(user.id)
            await message.answer(f"🔨 {user.full_name} забанен ({count}/{warn_limit})")
            await log_action(message.chat.id, "Бан за варны", user, message.from_user, reason)
            db.add_stat(message.chat.id, 'ban')
            db.clear_warns(message.chat.id, user.id)
        except Exception as e:
            await message.answer(f"❌ {e}")
    else:
        await message.answer(f"⚠️ {user.full_name} получил предупреждение ({count}/{warn_limit})\nПричина: {reason}")
        await log_action(message.chat.id, f"Варн {count}/{warn_limit}", user, message.from_user, reason)
        db.add_stat(message.chat.id, 'warn')

@dp.message(Command('warns'))
async def cmd_warns(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return
    user = message.reply_to_message.from_user
    count = db.get_warns(message.chat.id, user.id)
    await message.answer(f"📊 У {user.full_name} {count} предупреждений")

@dp.message(Command('clear_warns'))
async def cmd_clear_warns(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return
    user = message.reply_to_message.from_user
    db.clear_warns(message.chat.id, user.id)
    await message.answer(f"✅ Предупреждения {user.full_name} очищены")

@dp.message(Command('whitelist_add'))
async def cmd_whitelist_add(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return
    user = message.reply_to_message.from_user
    db.add_to_whitelist(message.chat.id, user.id)
    await message.answer(f"✅ {user.full_name} добавлен в белый список")

@dp.message(Command('whitelist_remove'))
async def cmd_whitelist_remove(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return
    user = message.reply_to_message.from_user
    db.remove_from_whitelist(message.chat.id, user.id)
    await message.answer(f"✅ {user.full_name} удалён из белого списка")

@dp.message(Command('captcha'))
async def cmd_captcha(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ['on', 'off']:
        await message.answer("❌ Использование: /captcha on или /captcha off")
        return
    enabled = args[1].lower() == 'on'
    db.set_captcha_enabled(message.chat.id, enabled)
    await message.answer(f"✅ Капча {'включена' if enabled else 'выключена'}")

@dp.message(Command('toggle'))
async def cmd_toggle(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /toggle spam /toggle links /toggle swear")
        return

    toggle_map = {
        'spam': 'delete_spam',
        'links': 'delete_links',
        'swear': 'delete_swear'
    }
    if args[1] not in toggle_map:
        await message.answer("❌ Неизвестная опция. Доступно: spam, links, swear")
        return

    settings = db.get_settings(message.chat.id) or DEFAULT_SETTINGS.copy()
    key = toggle_map[args[1]]
    settings[key] = not settings.get(key, False)
    db.save_settings(message.chat.id, settings)
    await message.answer(f"✅ {args[1]} теперь {'включён' if settings[key] else 'выключен'}")

@dp.message(Command('set_welcome'))
async def cmd_set_welcome(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    text = message.text.replace('/set_welcome', '', 1).strip()
    if not text:
        await message.answer("❌ Использование: /set_welcome Добро пожаловать, {name}!")
        return
    settings = db.get_settings(message.chat.id) or DEFAULT_SETTINGS.copy()
    settings['welcome_text'] = text
    db.save_settings(message.chat.id, settings)
    await message.answer(f"✅ Текст приветствия обновлён:\n{text}")

@dp.message(Command('set_warnlimit'))
async def cmd_set_warnlimit(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /set_warnlimit 3")
        return
    try:
        limit = int(args[1])
        if limit < 1:
            raise ValueError
        settings = db.get_settings(message.chat.id) or DEFAULT_SETTINGS.copy()
        settings['warn_limit'] = limit
        db.save_settings(message.chat.id, settings)
        await message.answer(f"✅ Лимит предупреждений установлен: {limit}")
    except:
        await message.answer("❌ Введите число больше 0")

# ==================== СОБЫТИЯ ====================

@dp.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    chat_id = message.chat.id
    settings = db.get_settings(chat_id) or DEFAULT_SETTINGS.copy()

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        if settings.get('captcha_enabled'):
            code = generate_captcha()
            db.save_captcha(chat_id, user.id, code)
            try:
                await bot.send_message(
                    user.id,
                    f"🔐 <b>Подтверждение</b>\n\nВ группе {message.chat.title} включена защита.\n"
                    f"Введите код: <code>{code}</code>",
                    parse_mode='HTML'
                )
            except:
                await message.answer(f"{user.full_name}, напишите мне в ЛС для подтверждения.")
        elif settings.get('welcome_enabled'):
            welcome = settings.get('welcome_text', DEFAULT_SETTINGS['welcome_text'])
            await message.answer(welcome.replace('{name}', user.full_name))
            db.add_stat(chat_id, 'join')

@dp.message(F.left_chat_member)
async def on_user_left(message: types.Message):
    db.add_stat(message.chat.id, 'leave')

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def moderate_message(message: types.Message):
    if message.from_user.is_bot:
        return

    # Пропускаем админов и белый список
    if await is_admin(message.chat.id, message.from_user.id) or \
       db.is_whitelisted(message.chat.id, message.from_user.id):
        return

    # Проверка капчи
    if db.check_captcha(message.chat.id, message.from_user.id, message.text.strip()):
        await message.answer(f"✅ {message.from_user.full_name}, вы подтверждены!")
        db.add_stat(message.chat.id, 'captcha_ok')
        await message.delete()
        return

    settings = db.get_settings(message.chat.id) or DEFAULT_SETTINGS.copy()
    filters = ModerationFilters(settings)
    reasons = filters.check_message(message.text or "")

    if reasons:
        try:
            await message.delete()
            db.add_stat(message.chat.id, 'delete')
            warn_text = f"⚠️ {message.from_user.full_name}, удалено за: {', '.join(reasons)}"
            await message.answer(warn_text, delete_after=5)
        except Exception as e:
            print(f"Ошибка удаления: {e}")
