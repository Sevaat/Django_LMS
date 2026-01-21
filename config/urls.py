from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("course/", include("lms.urls", namespace="course")),
]
