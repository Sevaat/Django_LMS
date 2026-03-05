FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry через pip (намного быстрее и надежнее)
RUN pip install --no-cache-dir poetry==1.8.5

# Настраиваем Poetry
RUN poetry config virtualenvs.create false

# Копируем файлы с зависимостями
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем зависимости
RUN poetry install --no-interaction --no-ansi --no-root

# Копируем проект
COPY . /app/

# Создаем директории
RUN mkdir -p /app/static /app/media

# Команда запуска
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]