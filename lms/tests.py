from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from lms.models import Course, Lesson
from users.models import User, Subscription


class LessonTestCase(APITestCase):
    """
    Тестирование CRUD операций для уроков
    """

    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем группы
        self.moder_group = Group.objects.create(name='moders')

        # Создаем пользователей с разными ролями
        self.owner_user = User.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            first_name='Owner',
            last_name='User'
        )

        self.moder_user = User.objects.create_user(
            email='moder@test.com',
            password='testpass123',
            first_name='Moder',
            last_name='User'
        )
        self.moder_user.groups.add(self.moder_group)

        self.regular_user = User.objects.create_user(
            email='regular@test.com',
            password='testpass123',
            first_name='Regular',
            last_name='User'
        )

        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )

        # Создаем тестовый курс
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            owner=self.owner_user
        )

        # Создаем тестовый урок (принадлежит owner_user)
        self.lesson = Lesson.objects.create(
            name='Test Lesson',
            description='Test Lesson Description',
            video_link='https://www.youtube.com/watch?v=test123',
            course=self.course,
            owner=self.owner_user
        )

        # URL для различных операций
        self.lesson_list_url = reverse('lms:lesson_list')
        self.lesson_create_url = reverse('lms:lesson_create')
        self.lesson_detail_url = reverse('lms:lesson_retrieve', args=[self.lesson.id])
        self.lesson_update_url = reverse('lms:lesson_update', args=[self.lesson.id])
        self.lesson_delete_url = reverse('lms:lesson_destroy', args=[self.lesson.id])

        # Данные для создания нового урока
        self.new_lesson_data = {
            'name': 'New Lesson',
            'description': 'New Lesson Description',
            'video_link': 'https://www.youtube.com/watch?v=new123',
            'course': self.course.id
        }

        # Данные для обновления урока
        self.update_data = {
            'name': 'Updated Lesson',
            'description': 'Updated Description',
            'video_link': 'https://www.youtube.com/watch?v=updated123'
        }

    def test_lesson_list_authenticated(self):
        """Тест получения списка уроков для аутентифицированного пользователя"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.lesson_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_lesson_list_unauthenticated(self):
        """Тест получения списка уроков для неаутентифицированного пользователя"""
        response = self.client.get(self.lesson_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_retrieve_owner(self):
        """Тест просмотра урока владельцем"""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.lesson_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.lesson.name)
        self.assertEqual(response.data['owner'], self.owner_user.id)

    def test_lesson_retrieve_moderator(self):
        """Тест просмотра урока модератором"""
        self.client.force_authenticate(user=self.moder_user)
        response = self.client.get(self.lesson_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.lesson.name)

    def test_lesson_retrieve_regular_user_not_owner(self):
        """Тест просмотра урока обычным пользователем (не владельцем)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.lesson_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_create_regular_user(self):
        """Тест создания урока обычным пользователем"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.lesson_create_url, self.new_lesson_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        new_lesson = Lesson.objects.get(name='New Lesson')
        self.assertEqual(new_lesson.owner, self.regular_user)

    def test_lesson_create_moderator(self):
        """Тест создания урока модератором (должен быть запрещен)"""
        self.client.force_authenticate(user=self.moder_user)
        response = self.client.post(self.lesson_create_url, self.new_lesson_data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_create_unauthenticated(self):
        """Тест создания урока неаутентифицированным пользователем"""
        response = self.client.post(self.lesson_create_url, self.new_lesson_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_update_owner(self):
        """Тест обновления урока владельцем"""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.patch(self.lesson_update_url, self.update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, 'Updated Lesson')

    def test_lesson_update_moderator(self):
        """Тест обновления урока модератором"""
        self.client.force_authenticate(user=self.moder_user)
        response = self.client.patch(self.lesson_update_url, self.update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, 'Updated Lesson')

    def test_lesson_update_regular_user_not_owner(self):
        """Тест обновления урока обычным пользователем (не владельцем)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(self.lesson_update_url, self.update_data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.lesson.refresh_from_db()
        self.assertNotEqual(self.lesson.name, 'Updated Lesson')

    def test_lesson_delete_owner(self):
        """Тест удаления урока владельцем"""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.delete(self.lesson_delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_delete_moderator(self):
        """Тест удаления урока модератором (должен быть запрещен)"""
        self.client.force_authenticate(user=self.moder_user)
        response = self.client.delete(self.lesson_delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_delete_regular_user_not_owner(self):
        """Тест удаления урока обычным пользователем (не владельцем)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(self.lesson_delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)


class LessonValidationTestCase(APITestCase):
    """
    Тестирование валидации ссылок на видео
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            name='Test Course',
            owner=self.user
        )

        self.lesson_data = {
            'name': 'Test Lesson',
            'description': 'Test Description',
            'course': self.course.id
        }

        self.create_url = reverse('lms:lesson_create')

    def test_valid_youtube_url(self):
        """Тест создания урока с корректной YouTube ссылкой"""
        self.client.force_authenticate(user=self.user)

        valid_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ',
            'https://m.youtube.com/watch?v=dQw4w9WgXcQ'
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                self.lesson_data['video_link'] = url
                response = self.client.post(self.create_url, self.lesson_data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_url_not_youtube(self):
        """Тест создания урока с некорректной ссылкой (не YouTube)"""
        self.client.force_authenticate(user=self.user)

        invalid_urls = [
            'https://vimeo.com/123456',
            'https://rutube.ru/video/123/',
            'https://example.com/video.mp4'
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.lesson_data['video_link'] = url
                response = self.client.post(self.create_url, self.lesson_data)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_video_link(self):
        """Тест создания урока без ссылки на видео"""
        self.client.force_authenticate(user=self.user)
        self.lesson_data['video_link'] = ''
        response = self.client.post(self.create_url, self.lesson_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LessonPaginationTestCase(APITestCase):
    """
    Тестирование пагинации для уроков
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            name='Test Course',
            owner=self.user
        )

        # Создаем 15 уроков
        for i in range(15):
            Lesson.objects.create(
                name=f'Lesson {i}',
                description=f'Description {i}',
                video_link='https://www.youtube.com/watch?v=test',
                course=self.course,
                owner=self.user
            )

        self.list_url = reverse('lms:lesson_list')
        self.client.force_authenticate(user=self.user)

    def test_default_pagination(self):
        """Тест пагинации по умолчанию (5 элементов)"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_custom_page_size(self):
        """Тест кастомного размера страницы"""
        response = self.client.get(f"{self.list_url}?page_size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_second_page(self):
        """Тест второй страницы"""
        response = self.client.get(f"{self.list_url}?page=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['previous'])

    def test_max_page_size_limit(self):
        """Тест ограничения максимального размера страницы"""
        response = self.client.get(f"{self.list_url}?page_size=30")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)  # max_page_size = 20