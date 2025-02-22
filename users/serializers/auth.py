from rest_framework import serializers
from users.models.users import User
from users.models.auth import TimedAuthTokenPair


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email"]


class TimedAuthTokenPairSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = TimedAuthTokenPair
        fields = ["token", "refresh_token", "user", "expires_at"]


class TokenCreateRequestSerializer(serializers.Serializer):
    hq_token = serializers.CharField()


class ServiceUserAuthInvalidateRequestSerializer(serializers.Serializer):
    hq_user_id = serializers.CharField()


class VerifyTokenRequestSerializer(serializers.Serializer):
    token = serializers.CharField()


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
