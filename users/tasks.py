import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task
def deactivate_inactive_users():
    """
    Периодическая задача для деактивации пользователей,
    которые не заходили более месяца
    """
    logger.info("Начинаем проверку неактивных пользователей...")

    # Вычисляем дату месяц назад
    one_month_ago = timezone.now() - timedelta(days=30)

    # Находим активных пользователей, которые не заходили более месяца
    # или у которых last_login is None (никогда не заходили) и созданы более месяца назад
    inactive_users = User.objects.filter(is_active=True).filter(
        # Пользователи с last_login старше месяца
        last_login__lt=one_month_ago
    ) | User.objects.filter(
        # Пользователи, которые никогда не заходили и созданы более месяца назад
        is_active=True,
        last_login__isnull=True,
        date_joined__lt=one_month_ago,
    )

    # Исключаем суперпользователей и персонал (опционально)
    # inactive_users = inactive_users.exclude(is_superuser=True).exclude(is_staff=True)

    count = inactive_users.count()

    if count > 0:
        logger.info(f"Найдено {count} неактивных пользователей")

        # Сохраняем информацию о блокируемых пользователях для логирования
        deactivated_users = []

        for user in inactive_users:
            user.is_active = False
            user.save()
            deactivated_users.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "last_login": str(user.last_login) if user.last_login else "Never",
                    "date_joined": str(user.date_joined),
                }
            )
            logger.info(f"Деактивирован пользователь: {user.email} (последний вход: {user.last_login})")

        logger.info(f"Деактивировано {count} пользователей")
        return {"status": "success", "deactivated_count": count, "deactivated_users": deactivated_users}
    else:
        logger.info("Неактивных пользователей не найдено")
        return {"status": "success", "deactivated_count": 0, "message": "No inactive users found"}


@shared_task
def deactivate_specific_user(user_id):
    """
    Вспомогательная задача для деактивации конкретного пользователя
    Можно вызывать вручную при необходимости
    """
    try:
        user = User.objects.get(id=user_id, is_active=True)

        # Проверяем, что это не суперпользователь
        if user.is_superuser or user.is_staff:
            logger.warning(f"Попытка деактивации суперпользователя/персонала: {user.email}")
            return {"status": "error", "message": "Cannot deactivate superuser or staff"}

        user.is_active = False
        user.save()

        logger.info(f"Деактивирован пользователь: {user.email}")
        return {"status": "success", "user_id": user_id, "email": user.email}
    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден или уже неактивен")
        return {"status": "error", "message": f"User with id {user_id} not found or already inactive"}


@shared_task
def check_and_deactivate_inactive_users(days=30):
    """
    Более гибкая версия задачи с возможностью указать количество дней
    """
    logger.info(f"Начинаем проверку пользователей, неактивных более {days} дней...")

    cutoff_date = timezone.now() - timedelta(days=days)

    inactive_users = User.objects.filter(is_active=True).filter(last_login__lt=cutoff_date) | User.objects.filter(
        is_active=True, last_login__isnull=True, date_joined__lt=cutoff_date
    )

    # Исключаем суперпользователей и персонал
    inactive_users = inactive_users.exclude(is_superuser=True).exclude(is_staff=True)

    count = inactive_users.count()

    if count > 0:
        # Блокируем пользователей
        deactivated_ids = list(inactive_users.values_list("id", flat=True))
        inactive_users.update(is_active=False)

        logger.info(f"Деактивировано {count} пользователей")
        return {
            "status": "success",
            "deactivated_count": count,
            "deactivated_ids": deactivated_ids,
            "days_threshold": days,
        }

    return {"status": "success", "deactivated_count": 0, "days_threshold": days}


@shared_task
def send_warning_to_inactive_users(days_before_block=25):
    """
    Опционально: отправка предупреждения пользователям,
    которые скоро будут заблокированы
    """
    from django.conf import settings
    from django.core.mail import send_mail

    warning_date = timezone.now() - timedelta(days=days_before_block)

    users_to_warn = User.objects.filter(is_active=True, last_login__lt=warning_date) | User.objects.filter(
        is_active=True, last_login__isnull=True, date_joined__lt=warning_date
    )

    # Исключаем суперпользователей и персонал
    users_to_warn = users_to_warn.exclude(is_superuser=True).exclude(is_staff=True)

    warned_count = 0
    for user in users_to_warn:
        try:
            days_until_block = 30 - days_before_block
            send_mail(
                subject="Предупреждение о блокировке аккаунта",
                message=f"""Здравствуйте, {user.email}!

Вы не заходили в свой аккаунт более {days_before_block} дней.
Если вы не зайдете в течение следующих {days_until_block} дней,
ваш аккаунт будет заблокирован.

Для входа перейдите по ссылке: {settings.SITE_URL}/users/login/

С уважением,
Команда LMS Platform""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            warned_count += 1
            logger.info(f"Предупреждение отправлено пользователю: {user.email}")
        except Exception as e:
            logger.error(f"Ошибка при отправке предупреждения пользователю {user.email}: {str(e)}")

    return {"status": "success", "warned_count": warned_count}
