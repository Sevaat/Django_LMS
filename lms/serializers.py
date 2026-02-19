from drf_spectacular.utils import extend_schema_field
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from lms.models import Course, Lesson
from lms.validators import YouTubeURLValidator, LinkValidator, validate_youtube_url


class CourseSerializer(ModelSerializer):
    """Базовый сериализатор для курса"""

    class Meta:
        model = Course
        fields = "__all__"


class LessonSerializer(ModelSerializer):
    """Сериализатор для урока"""

    course = CourseSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = "__all__"

        validators = [
            LinkValidator(field='video_link')
        ]


class CourseDetailSerializer(ModelSerializer):
    """Детальный сериализатор для курса с информацией о подписке"""

    count_lessons = SerializerMethodField()
    lessons = LessonSerializer(source="lesson_set", many=True, read_only=True)
    is_subscribed = SerializerMethodField()

    @extend_schema_field(int)
    def get_count_lessons(self, obj):
        """Возвращает количество уроков в курсе"""

        return obj.lesson_set.count()

    @extend_schema_field(bool)
    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на этот курс"""

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscriptions.filter(user=request.user).exists()
        return False

    class Meta:
        model = Course
        fields = ("id", "name", "description", "image", "count_lessons", "lessons", "is_subscribed", "owner")
