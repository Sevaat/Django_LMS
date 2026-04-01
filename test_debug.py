import os

import django

from lms.models import Lesson
from lms.tests import LessonTestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


# Создаем экземпляр теста и запускаем setUp
test = LessonTestCase(methodName="test_lesson_list_authenticated")
test._pre_setup()
test.setUp()

print(f"Всего уроков после setUp: {Lesson.objects.count()}")
for lesson in Lesson.objects.all():
    print(f"Урок: {lesson.id} - {lesson.name} - владелец: {lesson.owner.email}")

test._post_teardown()
