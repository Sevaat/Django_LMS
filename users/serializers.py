from rest_framework.serializers import ModelSerializer

from users.models import Payment, User, Subscription


class PaymentSerializer(ModelSerializer):
    """Сериализатор для платежей"""

    class Meta:
        model = Payment
        fields = "__all__"


class UserProfileSerializer(ModelSerializer):
    """Сериализатор для профиля пользователя"""

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ("id",)

class SubscriptionSerializer(ModelSerializer):
    """Сериализатор для подписки"""

    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = ('user', 'created_at')
