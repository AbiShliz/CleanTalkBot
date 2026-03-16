import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_file='moderator.db'):
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self):
        """Создает соединение с БД"""
        return sqlite3.connect(self.db_file)
    
    def init_db(self):
        """Инициализация таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица настроек групп
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_settings (
                    chat_id INTEGER PRIMARY KEY,
                    settings TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица нарушителей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offenders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица статистики
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    date DATE DEFAULT CURRENT_DATE,
                    UNIQUE(chat_id, action, date)
                )
            ''')
            
            conn.commit()
    
    def get_settings(self, chat_id):
        """Получает настройки группы"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT settings FROM group_settings WHERE chat_id = ?',
                (chat_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
            return None
    
    def save_settings(self, chat_id, settings):
        """Сохраняет настройки группы"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO group_settings (chat_id, settings, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (chat_id, json.dumps(settings)))
            conn.commit()
    
    def add_offender(self, chat_id, user_id, username, reason):
        """Добавляет нарушителя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO offenders (chat_id, user_id, username, reason)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, user_id, username, reason))
            conn.commit()
    
    def add_stat(self, chat_id, action):
        """Добавляет статистику"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO stats (chat_id, action, count)
                VALUES (?, ?, 1)
                ON CONFLICT(chat_id, action, date) DO UPDATE SET
                count = count + 1
            ''', (chat_id, action))
            conn.commit()
    
    def get_stats(self, chat_id, days=7):
        """Получает статистику за последние N дней"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT action, SUM(count) as total
                FROM stats
                WHERE chat_id = ? AND date >= date('now', ?)
                GROUP BY action
            ''', (chat_id, f'-{days} days'))
            return cursor.fetchall()

# Создаем глобальный объект БД
db = Database()
