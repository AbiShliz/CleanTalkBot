import re
import asyncio
from datetime import datetime, timedelta

class ModerationFilters:
    def __init__(self, settings):
        self.settings = settings
    
    async def check_message(self, message, bot):
        """Проверяет сообщение на нарушение"""
        reasons = []
        
        # Проверка на спам
        if self.settings.get('delete_spam'):
            if await self._is_spam(message):
                reasons.append('spam')
        
        # Проверка на ссылки
        if self.settings.get('delete_links'):
            if self._has_links(message.text or ''):
                reasons.append('links')
        
        # Проверка на мат
        if self.settings.get('delete_swear'):
            if self._has_swear(message.text or ''):
                reasons.append('swear')
        
        # Проверка возраста аккаунта
        if self.settings.get('min_age_hours', 0) > 0:
            if await self._is_account_too_young(message.from_user):
                reasons.append('young_account')
        
        # Проверка фото в профиле
        if self.settings.get('min_photos', 0) > 0:
            if await self._has_no_photos(message.from_user, bot):
                reasons.append('no_photos')
        
        return reasons if reasons else None
    
    def _has_links(self, text):
        """Проверяет наличие ссылок"""
        if not text:
            return False
        
        # Паттерны для ссылок
        link_patterns = [
            r'https?://\S+',
            r't\.me/\S+',
            r'@\w+',
            r'(?:www\.)\S+',
            r'\S+\.(?:com|ru|org|net|io)\b'
        ]
        
        for pattern in link_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _has_swear(self, text):
        """Проверяет наличие мата (упрощенная версия)"""
        swear_words = [
            'хуй', 'пизд', 'бля', 'еба', 'нах', 'пидор',
            'cock', 'fuck', 'shit', 'asshole', 'dick'
        ]
        text_lower = text.lower()
        for word in swear_words:
            if word in text_lower:
                return True
        return False
    
    async def _is_spam(self, message):
        """Проверка на спам (повторяющиеся сообщения)"""
        # TODO: реализовать проверку истории сообщений
        return False
    
    async def _is_account_too_young(self, user):
        """Проверка возраста аккаунта"""
        if not user.id:
            return True
        
        # Примерная проверка (в реальности нужно через API)
        return False
    
    async def _has_no_photos(self, user, bot):
        """Проверка наличия фото в профиле"""
        try:
            photos = await bot.get_user_profile_photos(user.id)
            return photos.total_count < self.settings.get('min_photos', 0)
        except:
            return True
