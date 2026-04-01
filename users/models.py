from typing import Any

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from lms.models import Course, Lesson


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер пользователей без username"""

    def create_user(self, email, password=None, **extra_fields):
        """Создает пользователя с email в качестве основного идентификатора"""
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создает суперпользователя"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    email = models.EmailField(unique=True, verbose_name="Почта", help_text="Укажите почту")
    phone = models.CharField(
        max_length=35, verbose_name="Телефон", blank=True, null=True, help_text="Введите номер телефона"
    )
    avatar = models.ImageField(
        upload_to="users/avatars/", verbose_name="Аватар", blank=True, null=True, help_text="Загрузите аватар"
    )
    city = models.CharField(max_length=50, verbose_name="Город", blank=True, null=True, help_text="Введите город")

    token = models.CharField(max_length=100, verbose_name="Token", blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> Any:
        return self.email


class Payment(models.Model):
    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"

    PAYMENT_METHODS = (
        (CASH, "Наличные"),
        (TRANSFER, "Перевод на счет"),
        (CARD, "Банковская карта"),
    )

    PAYMENT_STATUS = (
        ("pending", "Ожидает оплаты"),
        ("succeeded", "Оплачено"),
        ("failed", "Ошибка оплаты"),
        ("refunded", "Возврат"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="payments"
    )
    pay_date = models.DateTimeField(verbose_name="Дата оплаты", auto_now_add=True)
    paid_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Оплаченный курс",
        related_name="course_payments",
    )
    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Оплаченный урок",
        related_name="lesson_payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма оплаты")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name="Способ оплаты")

    stripe_product_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID продукта в Stripe")
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID цены в Stripe")
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID сессии в Stripe")
    stripe_payment_intent_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID платежа в Stripe"
    )
    payment_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Ссылка на оплату")
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default="pending", verbose_name="Статус платежа"
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.get_payment_status_display()}"


class Subscription(models.Model):
    """Модель подписки пользователя на обновления курса"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="subscriptions"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Курс", related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.email} - {self.course.name}"
