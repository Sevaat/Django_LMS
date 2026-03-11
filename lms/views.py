from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from lms.models import Course, Lesson
from lms.paginators import CoursePaginator, LessonPaginator
from lms.serializers import CourseDetailSerializer, CourseSerializer, LessonSerializer
from users.permissions import IsModer, IsOwner, IsNotModer

from lms.tasks import send_course_update_notifications, update_course_statistics, send_lesson_created_notification


@extend_schema_view(
    list=extend_schema(summary="Список курсов", tags=['Courses']),
    retrieve=extend_schema(summary="Детальная информация о курсе", tags=['Courses']),
    create=extend_schema(summary="Создание курса", tags=['Courses']),
    update=extend_schema(summary="Полное обновление курса", tags=['Courses']),
    partial_update=extend_schema(summary="Частичное обновление курса", tags=['Courses']),
    destroy=extend_schema(summary="Удаление курса", tags=['Courses']),
)
class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Course.objects.none()

        if IsModer().has_permission(self.request, self):
            return Course.objects.all()

        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """При обновлении курса отправляем уведомления подписчикам"""
        course = serializer.save()

        # Асинхронно отправляем уведомления подписчикам
        send_course_update_notifications.delay(course.id)

        # Обновляем статистику
        update_course_statistics.delay(course.id)

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = (IsAuthenticated, IsNotModer)
        elif self.action in ['destroy']:
            self.permission_classes = (IsAuthenticated, IsOwner)
        elif self.action in ['update', 'partial_update', 'retrieve']:
            self.permission_classes = (IsAuthenticated, IsModer | IsOwner)
        elif self.action == 'list':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    pagination_class = CoursePaginator

@extend_schema_view(
    get=extend_schema(
        summary="Список уроков",
        description="Возвращает список всех уроков с пагинацией и возможностью фильтрации",
        tags=['Lessons'],
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
    post=extend_schema(
        summary="Создание урока",
        description="Создает новый урок. Доступно только для обычных пользователей (не модераторов)",
        tags=['Lessons'],
        request=LessonSerializer,
        responses={201: LessonSerializer}
    ),
)
class LessonCreateAPIView(CreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsNotModer)

    def perform_create(self, serializer):
        lesson = serializer.save(owner=self.request.user)
        # Отправляем уведомление о новом уроке
        send_lesson_created_notification.delay(lesson.id)
        # Обновляем статистику курса
        if lesson.course:
            update_course_statistics.delay(lesson.course.id)

@extend_schema_view(
    get=extend_schema(
        summary="Список уроков",
        description="Возвращает список всех уроков с пагинацией",
        tags=['Lessons']
    ),
)
class LessonListAPIView(ListAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LessonPaginator

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Lesson.objects.none()

        if IsModer().has_permission(self.request, self):
            return Lesson.objects.all()

        return Lesson.objects.filter(owner=user)

@extend_schema_view(
    get=extend_schema(
        summary="Детальная информация об уроке",
        description="Возвращает детальную информацию об уроке. Доступно владельцу или модератору",
        tags=['Lessons']
    ),
)
class LessonRetrieveAPIView(RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsModer | IsOwner)

@extend_schema_view(
    put=extend_schema(
        summary="Полное обновление урока",
        description="Полностью обновляет информацию об уроке. Доступно владельцу или модератору",
        tags=['Lessons']
    ),
    patch=extend_schema(
        summary="Частичное обновление урока",
        description="Частично обновляет информацию об уроке. Доступно владельцу или модератору",
        tags=['Lessons']
    ),
)
class LessonUpdateAPIView(UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsModer | IsOwner)

    def perform_update(self, serializer):
        lesson = serializer.save()
        # При обновлении урока также отправляем уведомление
        # (если урок привязан к курсу)
        if lesson.course:
            # Отправляем уведомление об обновлении курса
            send_course_update_notifications.delay(lesson.course.id)
            # Обновляем статистику
            update_course_statistics.delay(lesson.course.id)

@extend_schema_view(
    delete=extend_schema(
        summary="Удаление урока",
        description="Удаляет урок. Доступно только владельцу",
        tags=['Lessons']
    ),
)
class LessonDestroyAPIView(DestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsOwner)

    def perform_destroy(self, instance):
        course_id = instance.course.id if instance.course else None
        instance.delete()
        # Обновляем статистику курса после удаления урока
        if course_id:
            update_course_statistics.delay(course_id)
