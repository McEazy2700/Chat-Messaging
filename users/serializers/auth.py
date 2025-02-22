from rest_framework import serializers
from users.models.auth import TimedAuthTokenPair
from users.serializers.user import UserSerializer


class TimedAuthTokenPairSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = TimedAuthTokenPair
        fields = ["token", "refresh_token", "user", "expires_at", "user"]


class TokenCreateRequestSerializer(serializers.Serializer):
    hq_token = serializers.CharField()


class ServiceUserAuthInvalidateRequestSerializer(serializers.Serializer):
    hq_user_id = serializers.CharField()


class VerifyTokenRequestSerializer(serializers.Serializer):
    token = serializers.CharField()


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
