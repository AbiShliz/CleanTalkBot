
import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_file='moderator.db'):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_settings (
                    chat_id INTEGER PRIMARY KEY,
                    settings TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    chat_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (chat_id, user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS captcha (
                    chat_id INTEGER,
                    user_id INTEGER,
                    code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, user_id)
                )
            ''')
            conn.commit()

    # Settings
    def get_settings(self, chat_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT settings FROM group_settings WHERE chat_id = ?', (chat_id,))
            result = cursor.fetchone()
            return json.loads(result[0]) if result else None

    def save_settings(self, chat_id, settings):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO group_settings (chat_id, settings, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (chat_id, json.dumps(settings)))
            conn.commit()

    # Stats
    def add_stat(self, chat_id, action):
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT action, SUM(count) as total
                FROM stats
                WHERE chat_id = ? AND date >= date('now', ?)
                GROUP BY action
            ''', (chat_id, f'-{days} days'))
            return cursor.fetchall()

    # Warns
    def add_warn(self, chat_id, user_id, username, reason):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO warns (chat_id, user_id, username, reason)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, user_id, username, reason))
            conn.commit()
            cursor.execute(
                'SELECT COUNT(*) FROM warns WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            return cursor.fetchone()[0]

    def get_warns(self, chat_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM warns WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            return cursor.fetchone()[0]

    def clear_warns(self, chat_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM warns WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            conn.commit()

    # Whitelist
    def add_to_whitelist(self, chat_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO whitelist (chat_id, user_id) VALUES (?, ?)',
                (chat_id, user_id)
            )
            conn.commit()

    def remove_from_whitelist(self, chat_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM whitelist WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            conn.commit()

    def is_whitelisted(self, chat_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM whitelist WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            return cursor.fetchone() is not None

    # Captcha
    def set_captcha_enabled(self, chat_id, enabled):
        settings = self.get_settings(chat_id) or DEFAULT_SETTINGS.copy()
        settings['captcha_enabled'] = enabled
        self.save_settings(chat_id, settings)

    def save_captcha(self, chat_id, user_id, code):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO captcha (chat_id, user_id, code) VALUES (?, ?, ?)',
                (chat_id, user_id, code)
            )
            conn.commit()

    def check_captcha(self, chat_id, user_id, code):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT code FROM captcha WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            result = cursor.fetchone()
            if result and result[0] == code:
                cursor.execute(
                    'DELETE FROM captcha WHERE chat_id = ? AND user_id = ?',
                    (chat_id, user_id)
                )
                conn.commit()
                return True
            return False

db = Database()