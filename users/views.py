from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from users.filters import PaymentFilter
from users.models import Payment
from users.serializers import PaymentSerializer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ['pay_date']      # разрешаем сортировку по дате оплаты
    ordering = ['pay_date']             # сортировка по умолчанию (по возрастанию)