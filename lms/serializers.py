from rest_framework.serializers import ModelSerializer, SerializerMethodField

from lms.models import Course, Lesson
from lms.validators import YouTubeURLValidator, LinkValidator, validate_youtube_url


class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class LessonSerializer(ModelSerializer):
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = "__all__"

        validators = [
            LinkValidator(field='video_link')
        ]


class CourseDetailSerializer(ModelSerializer):
    count_lessons = SerializerMethodField()
    lessons = LessonSerializer(source="lesson_set", many=True, read_only=True)
    is_subscribed = SerializerMethodField()

    def get_count_lessons(self, obj):
        return obj.lesson_set.count()

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на этот курс"""

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscriptions.filter(user=request.user).exists()
        return False

    class Meta:
        model = Course
        fields = ("id", "name", "description", "image", "count_lessons", "lessons", "is_subscribed", "owner")
