import django_filters

from users.models import Payment


class PaymentFilter(django_filters.FilterSet):
    class Meta:
        model = Payment
        fields = [
            'paid_course',      # фильтр по курсу
            'paid_lesson',      # фильтр по уроку
            'payment_method',   # фильтр по способу оплаты
        ]