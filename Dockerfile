FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install --no-cache-dir poetry==1.8.5
RUN poetry config virtualenvs.create false

WORKDIR /app

# Копирование зависимостей
COPY pyproject.toml poetry.lock* /app/

# Установка зависимостей
RUN poetry install --no-interaction --no-ansi --no-root

# Копирование кода
COPY . /app/

# Создание директорий для статики и медиа
RUN mkdir -p /app/static /app/media /app/logs

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]