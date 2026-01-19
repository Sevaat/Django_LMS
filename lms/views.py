from rest_framework.viewsets import ModelViewSet

from lms.models import Course
from lms.serializers import CourseSerializer


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer