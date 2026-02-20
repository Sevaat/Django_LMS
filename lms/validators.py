import re
from urllib.parse import urlparse

from rest_framework.serializers import ValidationError


class YouTubeURLValidator:
    """Валидатор для проверки, что ссылка ведет только на YouTube."""

    def __call__(self, value):
        if not isinstance(value, str) or not value:
            return

        parsed_url = urlparse(value)

        if not parsed_url.netloc:
            raise ValidationError("Введите корректный URL адрес")

        allowed_domains = [
            'youtube.com',
            'www.youtube.com',
            'youtu.be',
            'www.youtu.be',
            'm.youtube.com',
            'youtube-nocookie.com',
            'www.youtube-nocookie.com'
        ]

        domain = parsed_url.netloc.lower()

        is_allowed = False
        for allowed_domain in allowed_domains:
            if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                is_allowed = True
                break

        if not is_allowed:
            raise ValidationError("Ссылки разрешены только на видеохостинг YouTube (youtube.com, youtu.be)")


def validate_youtube_url(value):
    """Функция-валидатор для проверки ссылок на YouTube."""

    if not value:  # пропускаем пустые значения
        return

    youtube_patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtu\.be/[\w-]+',
        r'^https?://(?:www\.)?m\.youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtube-nocookie\.com/embed/[\w-]+'
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, value):
            return

    raise ValidationError("Ссылка должна вести на YouTube (например: https://www.youtube.com/watch?v=...)")


class LinkValidator:
    """
    Универсальный валидатор для проверки полей с ссылками.
    Позволяет указать, какое поле проверять при использовании в Meta.validators
    """

    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        field_value = value.get(self.field)

        if not field_value:
            return

        youtube_validator = YouTubeURLValidator()
        youtube_validator(field_value)