from django.urls import path
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import PaymentViewSet, UserCreateAPIView, UserViewSet, SubscriptionAPIView, PaymentSuccessView, \
    PaymentCancelView

app_name = UsersConfig.name


router = SimpleRouter()
router.register("payments/", PaymentViewSet)
router.register("", UserViewSet)

urlpatterns = [
    path("register/", UserCreateAPIView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(permission_classes=(AllowAny,)), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(permission_classes=(AllowAny,)), name="token_refresh"),
    path("subscriptions/", SubscriptionAPIView.as_view(), name="subscriptions"),
    path("payments/success/", PaymentSuccessView.as_view(), name="payment_success"),
    path("payments/cancel/", PaymentCancelView.as_view(), name="payment_cancel"),
]

urlpatterns += router.urls
