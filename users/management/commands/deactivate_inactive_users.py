from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Деактивирует пользователей, которые не заходили более 30 дней"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=30, help="Количество дней неактивности для блокировки (по умолчанию: 30)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать пользователей, которые будут заблокированы, без фактической блокировки",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(f"Поиск пользователей, неактивных более {days} дней...")
        self.stdout.write(f"Дата отсечки: {cutoff_date}")

        # Находим неактивных пользователей
        inactive_users = User.objects.filter(is_active=True).filter(last_login__lt=cutoff_date) | User.objects.filter(
            is_active=True, last_login__isnull=True, date_joined__lt=cutoff_date
        )

        # Исключаем суперпользователей и персонал
        inactive_users = inactive_users.exclude(is_superuser=True).exclude(is_staff=True)

        count = inactive_users.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("Неактивных пользователей не найдено"))
            return

        self.stdout.write(f"Найдено {count} неактивных пользователей:")

        for user in inactive_users:
            last_login = user.last_login if user.last_login else "Никогда не заходил"
            self.stdout.write(f"  - {user.email} (последний вход: {last_login})")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry-run: {count} пользователей будут заблокированы"))
        else:
            # Блокируем пользователей
            deactivated_ids = list(inactive_users.values_list("id", flat=True))
            inactive_users.update(is_active=False)

            self.stdout.write(self.style.SUCCESS(f"Успешно деактивировано {count} пользователей"))

            with open("deactivated_users.log", "a") as f:
                f.write(f"\n{timezone.now()} - Деактивировано {count} пользователей\n")
                for user_id in deactivated_ids:
                    f.write(f"  - User ID: {user_id}\n")
