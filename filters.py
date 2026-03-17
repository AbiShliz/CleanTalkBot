import re

class ModerationFilters:
    def __init__(self, settings):
        self.settings = settings

    def check_message(self, text):
        if not text:
            return []

        reasons = []

        if self.settings.get('delete_spam'):
            if self._is_spam(text):
                reasons.append('спам')

        if self.settings.get('delete_links'):
            if self._has_links(text):
                reasons.append('ссылки')

        if self.settings.get('delete_swear'):
            if self._has_swear(text):
                reasons.append('мат')

        return reasons

    def _has_links(self, text):
        link_patterns = [
            r'https?://\S+',
            r't\.me/\S+',
            r'@\w+',
            r'\S+\.(com|ru|org|net|io)\b'
        ]
        text_lower = text.lower()
        for pattern in link_patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    def _has_swear(self, text):
        swear_words = ['хуй', 'пизд', 'бля', 'еба', 'нах', 'сука', 'падла', 'cock', 'fuck', 'shit']
        text_lower = text.lower()
        for word in swear_words:
            if word in text_lower:
                return True
        return False

    def _is_spam(self, text):
        if len(text) > 20:
            for i in range(len(text) - 3):
                if text[i] == text[i+1] == text[i+2] == text[i+3]:
                    return True
        return False