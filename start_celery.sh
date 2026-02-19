# Запуск Celery worker
celery -A config worker --loglevel=info

# В отдельном терминале запуск Celery beat
celery -A config beat --loglevel=info

# Или запуск вместе с flower для мониторинга
celery -A config flower --port=5555