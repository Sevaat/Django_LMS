import stripe
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from lms.models import Course
from users.filters import PaymentFilter
from users.models import Payment, User, Subscription
from users.paginators import UserPaginator, PaymentPaginator, SubscriptionPaginator
from users.serializers import PaymentSerializer, UserProfileSerializer, SubscriptionSerializer, PaymentStatusSerializer, \
    PaymentCreateSerializer
from users.services import StripeService, create_stripe_session, create_stripe_price, create_stripe_product

from users.tasks import send_payment_reminder


@extend_schema_view(
    list=extend_schema(
        summary="Список пользователей",
        description="Возвращает список всех пользователей. Доступно только администраторам",
        tags=['Users']
    ),
    retrieve=extend_schema(
        summary="Детальная информация о пользователе",
        description="Возвращает информацию о пользователе. Доступно администраторам или самому пользователю",
        tags=['Users']
    ),
)
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    pagination_class = UserPaginator

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated()]
        if self.action in ("list", "retrieve", "create"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(pk=user.pk)


@extend_schema_view(
    list=extend_schema(
        summary="Список платежей",
        description="Возвращает список всех платежей с возможностью фильтрации",
        tags=['Payments'],
    ),
    retrieve=extend_schema(
        summary="Детальная информация о платеже",
        description="Возвращает информацию о конкретном платеже",
        tags=['Payments']
    ),
    create=extend_schema(
        summary="Создание платежа",
        description="Создает новый платеж и формирует ссылку на оплату через Stripe",
        tags=['Payments'],
        request=PaymentCreateSerializer,
        responses={201: PaymentSerializer}
    ),
)
class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = PaymentPaginator
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["pay_date"]
    ordering = ["pay_date"]

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    def perform_create(self, serializer):
        """Создание платежа с интеграцией Stripe"""
        payment = serializer.save(user=self.request.user)

        try:
            # Определяем, что оплачивается (курс или урок)
            if payment.paid_course:
                item = payment.paid_course
                item_name = f"Курс: {item.name}"
            else:
                item = payment.paid_lesson
                item_name = f"Урок: {item.name}"

            # Создаем продукт в Stripe
            product = create_stripe_product(item)

            # Создаем цену в Stripe
            price = create_stripe_price(float(payment.amount), product.id)

            # Сохраняем Stripe IDs
            payment.stripe_product_id = product.id
            payment.stripe_price_id = price.id
            payment.save()

            # Создаем сессию для оплаты
            session = create_stripe_session(price.id, payment.id)

            # Обновляем платеж с данными сессии
            payment.stripe_session_id = session.id
            payment.payment_url = session.url
            payment.save()

            # Планируем отправку напоминания через 1 час
            send_payment_reminder.apply_async(
                args=[payment.id],
                countdown=3600  # 1 час в секундах
            )

        except Exception as e:
            payment.payment_status = 'failed'
            payment.save()
            raise serializers.ValidationError(f"Ошибка при создании платежа в Stripe: {str(e)}")

    @extend_schema(
        summary="Проверка статуса платежа",
        description="Проверяет статус платежа в Stripe и обновляет его в базе данных",
        tags=['Payments'],
        responses={200: PaymentStatusSerializer}
    )
    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        """Проверка статуса платежа"""
        payment = self.get_object()

        if payment.stripe_session_id:
            try:
                # Получаем информацию о сессии из Stripe
                session = StripeService.retrieve_session(payment.stripe_session_id)

                # Обновляем статус платежа
                if session.payment_status == 'paid':
                    payment.payment_status = 'succeeded'
                elif session.payment_status == 'unpaid':
                    payment.payment_status = 'pending'
                elif session.status == 'expired':
                    payment.payment_status = 'failed'

                # Сохраняем ID платежного намерения
                if session.payment_intent:
                    payment.stripe_payment_intent_id = session.payment_intent

                payment.save()

            except stripe.error.StripeError as e:
                return Response(
                    {"error": f"Ошибка при проверке статуса: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = PaymentStatusSerializer(payment)
        return Response(serializer.data)


@extend_schema(
    summary="Регистрация пользователя",
    description="Создает нового пользователя. Доступно всем (без аутентификации)",
    request=UserProfileSerializer,
    responses={201: UserProfileSerializer},
    tags=['Auth']
)
class UserCreateAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()


@extend_schema_view(
    post=extend_schema(
        summary="Управление подпиской",
        description="Создает или удаляет подписку на курс",
        tags=['Subscriptions'],
    ),
    get=extend_schema(
        summary="Список подписок",
        description="Возвращает список подписок текущего пользователя",
        tags=['Subscriptions'],
    ),
)
class SubscriptionAPIView(APIView):
    """
    API view для управления подписками пользователя на курсы
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "Не указан ID курса"},
                status=400
            )

        course = get_object_or_404(Course, id=course_id)
        subscription = Subscription.objects.filter(user=user, course=course)

        if subscription.exists():
            subscription.delete()
            message = 'Подписка удалена'
            status_code = 200
        else:
            Subscription.objects.create(user=user, course=course)
            message = 'Подписка добавлена'
            status_code = 201

        return Response(
            {"message": message, "course_id": course_id},
            status=status_code
        )

    def get(self, request, *args, **kwargs):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)

        paginator = SubscriptionPaginator()
        page = paginator.paginate_queryset(subscriptions, request)

        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)


class PaymentSuccessView(APIView):
    """
    View для обработки успешной оплаты (редирект из Stripe)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        session_id = request.GET.get('session_id')

        if session_id:
            try:
                # Получаем сессию из Stripe
                session = StripeService.retrieve_session(session_id)

                # Находим платеж по client_reference_id
                payment_id = session.client_reference_id
                if payment_id:
                    payment = Payment.objects.get(id=payment_id)
                    payment.payment_status = 'succeeded'
                    payment.save()

                    return Response({
                        "message": "Платеж успешно выполнен",
                        "payment_id": payment.id,
                        "status": "success"
                    })
            except Exception as e:
                return Response({
                    "error": str(e)
                }, status=400)

        return Response({
            "message": "Платеж обработан"
        })


class PaymentCancelView(APIView):
    """
    View для обработки отмены оплаты (редирект из Stripe)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "message": "Платеж отменен"
        })
