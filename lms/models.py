from typing import Any

from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название", help_text="Укажите название курса")
    description = models.CharField(max_length=500, verbose_name="Описание", help_text="Укажите описание курса")
    image = models.ImageField(
        upload_to="course/preview", blank=True, null=True, verbose_name="Превью", help_text="Добавьте превью курса"
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Владелец",
        help_text="Укажите владельца курса",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["name"]

    def __str__(self) -> Any:
        return self.name


class Lesson(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название", help_text="Укажите название урока")
    description = models.CharField(max_length=500, verbose_name="Описание", help_text="Укажите описание урока")
    image = models.ImageField(
        upload_to="lesson/preview", blank=True, null=True, verbose_name="Превью", help_text="Добавьте превью урока"
    )
    video_link = models.CharField(
        max_length=200, verbose_name="Ссылка на видео", help_text="Укажите ссылку на видеоматериал"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Курс",
        help_text="Укажите принадлежность к курсу",
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Владелец",
        help_text="Укажите владельца урока",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["name", "course"]

    def __str__(self) -> Any:
        return self.name
