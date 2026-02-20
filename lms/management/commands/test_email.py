from django.core.management.base import BaseCommand
from lms.tasks import send_course_update_notifications
from lms.models import Course


class Command(BaseCommand):
    help = 'Тестирование отправки email уведомлений'

    def add_arguments(self, parser):
        parser.add_argument('course_id', type=int, help='ID курса для тестирования')

    def handle(self, *args, **options):
        course_id = options['course_id']

        try:
            course = Course.objects.get(id=course_id)
            self.stdout.write(f"Тестирование отправки уведомлений для курса: {course.name}")

            # Запускаем задачу синхронно для теста
            result = send_course_update_notifications(course_id)

            self.stdout.write(self.style.SUCCESS(f"Результат: {result}"))

        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Курс с ID {course_id} не найден"))