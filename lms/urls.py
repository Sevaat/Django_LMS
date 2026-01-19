from rest_framework.routers import SimpleRouter

from lms.views import CourseViewSet
from lms.apps import LmsConfig

app_name = LmsConfig.name


router = SimpleRouter()
router.register("", CourseViewSet)

urlpatterns = []

urlpatterns += router.urls