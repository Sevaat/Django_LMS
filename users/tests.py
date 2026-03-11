from unittest.mock import patch, MagicMock

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course
from users.models import User, Subscription, Payment
from users.services import StripeService


class SubscriptionTestCase(APITestCase):
    """
    Тестирование функционала подписок на курсы
    """

    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )

        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )

        self.moder_group = Group.objects.create(name='moders')
        self.moder_user = User.objects.create_user(
            email='moder@test.com',
            password='testpass123'
        )
        self.moder_user.groups.add(self.moder_group)

        # Создаем курсы
        self.course1 = Course.objects.create(
            name='Python Course',
            description='Learn Python',
            owner=self.user2  # Владелец - user2
        )

        self.course2 = Course.objects.create(
            name='Java Course',
            description='Learn Java',
            owner=self.user1
        )

        # Создаем подписку для user1 на course1
        self.subscription = Subscription.objects.create(
            user=self.user1,
            course=self.course1
        )

        # URL для работы с подписками
        self.subscriptions_url = reverse('users:subscriptions')

        # Данные для создания/удаления подписки
        self.subscription_data = {
            'course_id': self.course2.id
        }

    def test_subscription_create_authenticated(self):
        """Тест создания подписки аутентифицированным пользователем"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.subscriptions_url, self.subscription_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Подписка добавлена')
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user2,
                course=self.course2
            ).exists()
        )

    def test_subscription_create_unauthenticated(self):
        """Тест создания подписки неаутентифицированным пользователем"""
        response = self.client.post(self.subscriptions_url, self.subscription_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscription_create_without_course_id(self):
        """Тест создания подписки без указания course_id"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.subscriptions_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_subscription_create_nonexistent_course(self):
        """Тест создания подписки на несуществующий курс"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.subscriptions_url, {'course_id': 999})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_delete_existing(self):
        """Тест удаления существующей подписки"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            self.subscriptions_url,
            {'course_id': self.course1.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка удалена')
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user1,
                course=self.course1
            ).exists()
        )

    def test_subscription_toggle_create_delete(self):
        """Тест переключения подписки (создание/удаление)"""
        self.client.force_authenticate(user=self.user2)

        # Создаем подписку
        response1 = self.client.post(self.subscriptions_url, self.subscription_data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data['message'], 'Подписка добавлена')

        # Удаляем ту же подписку
        response2 = self.client.post(self.subscriptions_url, self.subscription_data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['message'], 'Подписка удалена')

    def test_subscription_list_authenticated(self):
        """Тест получения списка подписок пользователя"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.subscriptions_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['course'], self.course1.id)
        self.assertEqual(response.data['count'], 1)

    def test_subscription_list_unauthenticated(self):
        """Тест получения списка подписок без аутентификации"""
        response = self.client.get(self.subscriptions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscription_list_pagination(self):
        """Тест пагинации списка подписок"""
        # Создаем еще подписки для user1
        courses = []
        for i in range(10):
            course = Course.objects.create(
                name=f'Course {i}',
                owner=self.user1
            )
            courses.append(course)
            Subscription.objects.create(user=self.user1, course=course)

        self.client.force_authenticate(user=self.user1)

        # Проверяем первую страницу (5 элементов)
        response = self.client.get(self.subscriptions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 11)  # 1 старая + 10 новых
        self.assertIsNotNone(response.data['next'])

        # Проверяем вторую страницу
        response = self.client.get(f"{self.subscriptions_url}?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['previous'])

    def test_course_detail_with_subscription_flag(self):
        """Тест наличия флага подписки в детальной информации о курсе"""
        self.client.force_authenticate(user=self.user1)

        # Используем course2, где владелец - user1
        url = reverse('lms:course-detail', args=[self.course2.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # У user1 нет подписки на course2
        self.assertFalse(response.data['is_subscribed'])

    def test_course_detail_subscription_flag_another_user(self):
        """Тест флага подписки для другого пользователя"""
        self.client.force_authenticate(user=self.user2)

        # user2 - владелец course1, но не подписан на него
        url = reverse('lms:course-detail', args=[self.course1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_subscribed'])

    def test_course_detail_unauthenticated(self):
        """Тест отсутствия флага подписки для неаутентифицированного пользователя"""
        url = reverse('lms:course-detail', args=[self.course1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscription_unique_constraint(self):
        """Тест уникальности пары пользователь-курс"""
        # Пытаемся создать дубликат подписки
        with self.assertRaises(Exception):
            Subscription.objects.create(
                user=self.user1,
                course=self.course1
            )

    def test_subscription_str_method(self):
        """Тест строкового представления подписки"""
        expected_str = f"{self.user1.email} - {self.course1.name}"
        self.assertEqual(str(self.subscription), expected_str)


class SubscriptionPermissionsTestCase(APITestCase):
    """
    Тестирование прав доступа для подписок
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123'
        )

        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            name='Test Course',
            owner=self.user
        )

        self.subscription = Subscription.objects.create(
            user=self.user,
            course=self.course
        )

        self.subscriptions_url = reverse('users:subscriptions')

    def test_user_can_only_see_own_subscriptions(self):
        """Тест, что пользователь видит только свои подписки"""
        # Создаем подписку для другого пользователя
        Subscription.objects.create(
            user=self.other_user,
            course=self.course
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.subscriptions_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)

    def test_user_cannot_manage_subscriptions_for_other_users(self):
        """Тест, что пользователь не может управлять подписками других пользователей"""
        self.client.force_authenticate(user=self.other_user)

        # Пытаемся удалить подписку user (не свою)
        response = self.client.post(
            self.subscriptions_url,
            {'course_id': self.course.id}
        )

        # Должна создаться новая подписка для other_user, а не удалиться подписка user
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.other_user,
                course=self.course
            ).exists()
        )
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                course=self.course
            ).exists()
        )


class StripeServiceTestCase(TestCase):
    """
    Тесты для сервиса Stripe
    """

    def setUp(self):
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description'
        )

    @patch('stripe.Product.create')
    def test_create_product(self, mock_product_create):
        """Тест создания продукта в Stripe"""
        mock_product = MagicMock()
        mock_product.id = 'prod_test123'
        mock_product.name = 'Test Course'
        mock_product_create.return_value = mock_product

        product = StripeService.create_product(
            name='Test Course',
            description='Test Description'
        )

        self.assertEqual(product.id, 'prod_test123')
        mock_product_create.assert_called_once_with(
            name='Test Course',
            description='Test Description',
            type='good'
        )

    @patch('stripe.Price.create')
    def test_create_price(self, mock_price_create):
        """Тест создания цены в Stripe"""
        mock_price = MagicMock()
        mock_price.id = 'price_test123'
        mock_price.unit_amount = 10000
        mock_price_create.return_value = mock_price

        price = StripeService.create_price(
            amount=100.00,
            currency='rub',
            product_id='prod_test123'
        )

        self.assertEqual(price.id, 'price_test123')
        mock_price_create.assert_called_once_with(
            unit_amount=10000,
            currency='rub',
            product='prod_test123'
        )

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_session_create):
        """Тест создания сессии оплаты"""
        mock_session = MagicMock()
        mock_session.id = 'session_test123'
        mock_session.url = 'https://checkout.stripe.com/session_test123'
        mock_session_create.return_value = mock_session

        session = StripeService.create_checkout_session(
            price_id='price_test123',
            success_url='http://localhost/success/',
            cancel_url='http://localhost/cancel/',
            client_reference_id='1'
        )

        self.assertEqual(session.id, 'session_test123')
        mock_session_create.assert_called_once()


class PaymentIntegrationTestCase(APITestCase):
    """
    Тесты интеграции платежей
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            owner=self.user  # Владелец - текущий пользователь
        )

        self.client.force_authenticate(user=self.user)
        self.payment_url = reverse('users:payment-list')

    @patch('users.views.create_stripe_product')
    @patch('users.views.create_stripe_price')
    @patch('users.views.create_stripe_session')
    def test_create_payment_with_stripe(self, mock_session, mock_price, mock_product):
        """Тест создания платежа с интеграцией Stripe"""
        mock_product.return_value = MagicMock(id='prod_test123')
        mock_price.return_value = MagicMock(id='price_test123')

        mock_session_obj = MagicMock()
        mock_session_obj.id = 'session_test123'
        mock_session_obj.url = 'https://checkout.stripe.com/session_test123'
        mock_session.return_value = mock_session_obj

        data = {
            'paid_course': self.course.id,
            'amount': 1000.00,
            'payment_method': 'card'
        }

        response = self.client.post(self.payment_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)

        payment = Payment.objects.first()
        self.assertEqual(payment.stripe_product_id, 'prod_test123')
        self.assertEqual(payment.stripe_price_id, 'price_test123')
        self.assertEqual(payment.stripe_session_id, 'session_test123')
        self.assertEqual(payment.payment_status, 'pending')