from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from users.models import Payment, Subscription, User


class PaymentSerializer(ModelSerializer):
    """Сериализатор для платежей"""

    payment_url = SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "pay_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "payment_url",
            "payment_status",
            "stripe_session_id",
            "stripe_payment_intent_id",
        ]
        read_only_fields = ("pay_date", "payment_status", "payment_url")

    @extend_schema_field(str)
    def get_payment_url(self, obj):
        """Возвращает ссылку на оплату"""
        return obj.payment_url


class PaymentCreateSerializer(ModelSerializer):
    """Сериализатор для создания платежа"""

    class Meta:
        model = Payment
        fields = ["paid_course", "paid_lesson", "amount", "payment_method"]

    def validate(self, data):
        """Валидация данных перед созданием платежа"""
        # Проверяем, что указан либо курс, либо урок
        if not data.get("paid_course") and not data.get("paid_lesson"):
            raise serializers.ValidationError("Необходимо указать либо оплачиваемый курс, либо урок")

        # Проверяем, что курс/урок существует
        if data.get("paid_course") and data.get("paid_lesson"):
            raise serializers.ValidationError("Нельзя оплатить одновременно курс и урок")

        # Проверяем сумму
        if data.get("amount") <= 0:
            raise serializers.ValidationError("Сумма оплаты должна быть положительной")

        return data


class PaymentStatusSerializer(ModelSerializer):
    """Сериализатор для статуса платежа"""

    class Meta:
        model = Payment
        fields = ["id", "payment_status", "payment_url"]


class UserProfileSerializer(ModelSerializer):
    """Сериализатор для профиля пользователя"""

    class Meta:
        model = User
        fields = ("id", "email", "phone", "avatar", "city", "first_name", "last_name", "password")
        read_only_fields = ("id",)
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        """Создание пользователя с хешированием пароля"""
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SubscriptionSerializer(ModelSerializer):
    """Сериализатор для подписки"""

    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = ("user", "created_at")
