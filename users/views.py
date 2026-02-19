from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
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
from users.serializers import PaymentSerializer, UserProfileSerializer, SubscriptionSerializer

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
    update=extend_schema(
        summary="Обновление пользователя",
        description="Обновляет информацию о пользователе. Доступно только аутентифицированным пользователям",
        tags=['Users']
    ),
    partial_update=extend_schema(
        summary="Частичное обновление пользователя",
        description="Частично обновляет информацию о пользователе",
        tags=['Users']
    ),
    destroy=extend_schema(
        summary="Удаление пользователя",
        description="Удаляет пользователя. Доступно только аутентифицированным пользователям",
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
        description="Возвращает список всех платежей с возможностью фильтрации по курсу, уроку и способу оплаты",
        tags=['Payments'],
        parameters=[
            OpenApiParameter(
                name='paid_course',
                description='Фильтр по ID курса',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='paid_lesson',
                description='Фильтр по ID урока',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='payment_method',
                description='Фильтр по способу оплаты (cash/transfer)',
                required=False,
                type=str,
                enum=['cash', 'transfer']
            ),
            OpenApiParameter(
                name='ordering',
                description='Сортировка по дате (pay_date или -pay_date)',
                required=False,
                type=str
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Детальная информация о платеже",
        description="Возвращает информацию о конкретном платеже",
        tags=['Payments']
    ),
    create=extend_schema(
        summary="Создание платежа",
        description="Создает новый платеж",
        tags=['Payments']
    ),
    update=extend_schema(
        summary="Обновление платежа",
        description="Полностью обновляет информацию о платеже",
        tags=['Payments']
    ),
    partial_update=extend_schema(
        summary="Частичное обновление платежа",
        description="Частично обновляет информацию о платеже",
        tags=['Payments']
    ),
    destroy=extend_schema(
        summary="Удаление платежа",
        description="Удаляет платеж",
        tags=['Payments']
    ),
)
class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = PaymentPaginator

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["pay_date"]  # разрешаем сортировку по дате оплаты
    ordering = ["pay_date"]  # сортировка по умолчанию (по возрастанию)

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
        description="Создает или удаляет подписку на курс. Если подписка существует - удаляет, если нет - создает",
        tags=['Subscriptions'],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "ID курса"
                    }
                },
                "required": ["course_id"]
            }
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={'course_id': 1},
                request_only=True
            ),
            OpenApiExample(
                'Пример ответа (создание)',
                value={'message': 'Подписка добавлена', 'course_id': 1},
                response_only=True,
                status_codes=['201']
            ),
            OpenApiExample(
                'Пример ответа (удаление)',
                value={'message': 'Подписка удалена', 'course_id': 1},
                response_only=True,
                status_codes=['200']
            ),
        ]
    ),
    get=extend_schema(
        summary="Список подписок",
        description="Возвращает список подписок текущего пользователя с пагинацией",
        tags=['Subscriptions'],
        parameters=[
            OpenApiParameter(
                name='page',
                description='Номер страницы',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='page_size',
                description='Количество элементов на странице',
                required=False,
                type=int
            ),
        ]
    ),
)
class SubscriptionAPIView(APIView):
    """API view для управления подписками пользователя на курсы"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST запрос для создания или удаления подписки. Ожидает в теле запроса: {"course_id": 1}"""
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
        """GET запрос для получения всех подписок пользователя"""

        user = request.user
        subscriptions = Subscription.objects.filter(user=user)

        paginator = SubscriptionPaginator()
        page = paginator.paginate_queryset(subscriptions, request)

        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
