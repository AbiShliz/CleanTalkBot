#!/bin/bash

echo "🚀 Установка бота-модератора..."

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Создаем виртуальное окружение
echo "📦 Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаю зависимости..."
pip install -r requirements.txt

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден. Создаю шаблон..."
    echo "BOT_TOKEN=ваш_токен_здесь" > .env
    echo "✏️ Отредактируйте .env и добавьте токен бота"
fi

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Для запуска бота:"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo ""
echo "Для запуска в фоне (через tmux):"
echo "   tmux new -s bot"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo "   Ctrl+B, D - отключиться"
