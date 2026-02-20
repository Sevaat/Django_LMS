import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр Celery
app = Celery('config')

# Загружаем конфигурацию из настроек Django с префиксом CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим и регистрируем задачи из всех приложений
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Импортируем настройки Django для доступа к TIME_ZONE
from django.conf import settings

# Явно указываем настройки для Celery Beat
app.conf.beat_schedule = {
    'check-inactive-users': {
        'task': 'users.tasks.deactivate_inactive_users',
        'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
    },
    'check-pending-payments': {
        'task': 'users.tasks.check_pending_payments',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
    },
    'clean-expired-subscriptions': {
        'task': 'users.tasks.clean_expired_subscriptions',
        'schedule': crontab(hour=2, minute=0),  # Каждый день в 2:00
    },
    'send-daily-course-summary': {
        'task': 'lms.tasks.send_daily_course_summary',
        'schedule': crontab(hour=8, minute=0),  # Каждый день в 8:00
    },
}

# Устанавливаем timezone из настроек Django
app.conf.timezone = settings.TIME_ZONE