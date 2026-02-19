from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from lms.models import Course, Lesson
from lms.paginators import CoursePaginator, LessonPaginator
from lms.serializers import CourseDetailSerializer, CourseSerializer, LessonSerializer
from users.permissions import IsModer, IsOwner


@extend_schema_view(
    list=extend_schema(
        summary="Список курсов",
        description="Возвращает список всех курсов с пагинацией",
        tags=['Courses']
    ),
    retrieve=extend_schema(
        summary="Детальная информация о курсе",
        description="Возвращает детальную информацию о курсе, включая список уроков и статус подписки",
        tags=['Courses']
    ),
    create=extend_schema(
        summary="Создание курса",
        description="Создает новый курс. Доступно только для обычных пользователей (не модераторов)",
        tags=['Courses'],
        request=CourseSerializer,
        responses={201: CourseSerializer}
    ),
    update=extend_schema(
        summary="Полное обновление курса",
        description="Полностью обновляет информацию о курсе. Доступно владельцу или модератору",
        tags=['Courses']
    ),
    partial_update=extend_schema(
        summary="Частичное обновление курса",
        description="Частично обновляет информацию о курсе. Доступно владельцу или модератору",
        tags=['Courses']
    ),
    destroy=extend_schema(
        summary="Удаление курса",
        description="Удаляет курс. Доступно только владельцу",
        tags=['Courses']
    ),
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

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = (IsAuthenticated, ~IsModer,)
        elif self.action in ['destroy', 'retrieve']:
            self.permission_classes = (IsAuthenticated, IsOwner)
        elif self.action in ['update', 'partial_update']:
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
    permission_classes = (IsAuthenticated, ~IsModer)

    def perform_create(self, serializer):
        lesson = serializer.save()
        lesson.owner = self.request.user
        lesson.save()

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
    permission_classes = (IsAuthenticated, IsOwner)

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
