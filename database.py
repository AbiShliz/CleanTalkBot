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
            conn.commit()
    
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

db = Database()
