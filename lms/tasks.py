import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_notifications(course_id):
    """
    Асинхронная задача для отправки уведомлений подписчикам об обновлении курса
    """
    from lms.models import Course
    from users.models import Subscription

    try:
        course = Course.objects.get(id=course_id)
        logger.info(f"Начинаем отправку уведомлений для курса '{course.name}' (ID: {course_id})")

        # Находим всех подписчиков курса
        subscribers = Subscription.objects.filter(course=course).select_related("user")

        if not subscribers.exists():
            logger.info(f"Нет подписчиков для курса '{course.name}'")
            return f"Нет подписчиков для курса {course_id}"

        # Формируем ссылку на курс
        course_url = f"{settings.SITE_URL}{reverse('lms:course-detail', args=[course.id])}"

        # Счетчики для статистики
        successful = 0
        failed = 0

        for subscription in subscribers:
            user = subscription.user
            try:
                # Формируем контекст для письма
                context = {"user": user, "course": course, "course_url": course_url, "site_url": settings.SITE_URL}

                # Рендерим HTML письмо
                html_message = render_to_string("emails/course_update.html", context)
                plain_message = strip_tags(html_message)

                # Отправляем письмо
                send_mail(
                    subject=f"Обновление курса: {course.name}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                logger.info(f"Уведомление отправлено пользователю {user.email}")
                successful += 1

            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {user.email}: {str(e)}")
                failed += 1

        logger.info(f"Отправка уведомлений завершена. Успешно: {successful}, Ошибок: {failed}")
        return f"Уведомления отправлены: успешно={successful}, ошибок={failed}"

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден")
        return f"Ошибка: курс {course_id} не найден"
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке уведомлений: {str(e)}")
        return f"Ошибка при отправке уведомлений: {str(e)}"


@shared_task
def send_course_update_batch(course_ids):
    """
    Отправка уведомлений для нескольких курсов (для массовых обновлений)
    """
    results = []
    for course_id in course_ids:
        result = send_course_update_notifications.delay(course_id)
        results.append(result.id)

    return f"Запущена отправка для {len(results)} курсов: {results}"


@shared_task
def send_lesson_created_notification(lesson_id):
    """
    Отправка уведомления о создании нового урока
    """
    from lms.models import Lesson
    from users.models import Subscription

    try:
        lesson = Lesson.objects.select_related("course", "owner").get(id=lesson_id)

        if not lesson.course:
            logger.info(f"Урок {lesson_id} не привязан к курсу, уведомления не отправляются")
            return f"Урок {lesson_id} не привязан к курсу"

        # Находим подписчиков курса
        subscribers = Subscription.objects.filter(course=lesson.course).select_related("user")

        if not subscribers.exists():
            logger.info(f"Нет подписчиков для курса '{lesson.course.name}'")
            return f"Нет подписчиков для курса {lesson.course.id}"

        # Формируем ссылку на урок
        lesson_url = f"{settings.SITE_URL}{reverse('lms:lesson_retrieve', args=[lesson.id])}"

        successful = 0
        failed = 0

        for subscription in subscribers:
            user = subscription.user
            try:
                context = {
                    "user": user,
                    "lesson": lesson,
                    "course": lesson.course,
                    "lesson_url": lesson_url,
                    "site_url": settings.SITE_URL,
                    "is_new_lesson": True,
                }

                html_message = render_to_string("emails/new_lesson.html", context)
                plain_message = strip_tags(html_message)

                send_mail(
                    subject=f"Новый урок в курсе '{lesson.course.name}': {lesson.name}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                successful += 1

            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {str(e)}")
                failed += 1

        logger.info(f"Уведомления о новом уроке отправлены: успешно={successful}, ошибок={failed}")
        return f"Уведомления о новом уроке отправлены: успешно={successful}, ошибок={failed}"

    except Lesson.DoesNotExist:
        logger.error(f"Урок {lesson_id} не найден")
        return f"Ошибка: урок {lesson_id} не найден"


@shared_task
def send_lesson_update_notification(lesson_id):
    """
    Отправка уведомления об обновлении существующего урока
    """
    from lms.models import Lesson
    from users.models import Subscription

    try:
        lesson = Lesson.objects.select_related("course", "owner").get(id=lesson_id)

        if not lesson.course:
            logger.info(f"Урок {lesson_id} не привязан к курсу, уведомления не отправляются")
            return f"Урок {lesson_id} не привязан к курсу"

        # Находим подписчиков курса
        subscribers = Subscription.objects.filter(course=lesson.course).select_related("user")

        if not subscribers.exists():
            logger.info(f"Нет подписчиков для курса '{lesson.course.name}'")
            return f"Нет подписчиков для курса {lesson.course.id}"

        # Формируем ссылку на урок
        lesson_url = f"{settings.SITE_URL}{reverse('lms:lesson_retrieve', args=[lesson.id])}"

        successful = 0
        failed = 0

        for subscription in subscribers:
            user = subscription.user
            try:
                context = {
                    "user": user,
                    "lesson": lesson,
                    "course": lesson.course,
                    "lesson_url": lesson_url,
                    "site_url": settings.SITE_URL,
                    "is_update": True,
                }

                html_message = render_to_string("emails/lesson_updated.html", context)
                plain_message = strip_tags(html_message)

                send_mail(
                    subject=f"Урок обновлен: {lesson.name} (Курс: {lesson.course.name})",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                successful += 1

            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {str(e)}")
                failed += 1

        logger.info(f"Уведомления об обновлении урока отправлены: успешно={successful}, ошибок={failed}")
        return f"Уведомления об обновлении урока отправлены: успешно={successful}, ошибок={failed}"

    except Lesson.DoesNotExist:
        logger.error(f"Урок {lesson_id} не найден")
        return f"Ошибка: урок {lesson_id} не найден"


@shared_task
def update_course_statistics(course_id):
    """
    Задача для обновления статистики курса
    """
    from lms.models import Course

    try:
        course = Course.objects.get(id=course_id)

        # Подсчитываем количество уроков
        lessons_count = course.lesson_set.count()

        # Подсчитываем количество подписчиков
        subscribers_count = course.subscriptions.count()

        logger.info(f"Статистика курса '{course.name}': уроков={lessons_count}, подписчиков={subscribers_count}")

        return {
            "course_id": course_id,
            "course_name": course.name,
            "lessons_count": lessons_count,
            "subscribers_count": subscribers_count,
        }

    except Course.DoesNotExist:
        logger.error(f"Курс {course_id} не найден")
        return f"Ошибка: курс {course_id} не найден"


@shared_task
def send_daily_course_summary():
    """
    Ежедневная рассылка сводки по обновлениям курсов
    """
    from lms.models import Course
    from users.models import Subscription

    logger.info("Начинаем ежедневную рассылку сводки по курсам")

    # Находим курсы, обновленные за последние 24 часа
    last_24h = timezone.now() - timedelta(hours=24)
    updated_courses = Course.objects.filter(updated_at__gte=last_24h)

    if not updated_courses.exists():
        logger.info("Нет обновленных курсов за последние 24 часа")
        return "Нет обновленных курсов"

    # Группируем подписчиков по курсам
    for course in updated_courses:
        subscribers = Subscription.objects.filter(course=course).select_related("user")

        for subscription in subscribers:
            user = subscription.user
            try:
                context = {
                    "user": user,
                    "course": course,
                    "updated_courses": updated_courses,
                    "site_url": settings.SITE_URL,
                }

                html_message = render_to_string("emails/daily_summary.html", context)
                plain_message = strip_tags(html_message)

                send_mail(
                    subject="Ежедневная сводка: обновления курсов",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                logger.info(f"Сводка отправлена пользователю {user.email}")

            except Exception as e:
                logger.error(f"Ошибка при отправке сводки пользователю {user.email}: {str(e)}")

    return f"Сводка отправлена для {updated_courses.count()} курсов"


@shared_task
def cleanup_old_notifications(days=30):
    """
    Очистка старых уведомлений (если храните их в БД)
    """

    try:
        logger.info(f"Очистка уведомлений старше {days} дней")
        return "Очистка завершена"

    except Exception as e:
        logger.error("Ошибка при очистке уведомлений: {str(e)}")
        return f"Ошибка: {str(e)}"
