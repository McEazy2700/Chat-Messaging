from django.utils import timezone
import jwt
import base64
import os
from typing import Any, cast
from rest_framework import viewsets
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import Request, Response, exceptions, status
from django.shortcuts import get_object_or_404
from django.conf import settings

from includes.serializers.response import MessageResponseSerializer
from users.models.auth import TimedAuthTokenPair
from users.models.users import User
from users.permissions.auth import BaseAuthServicePermissions
from users.serializers.auth import (
    RefreshTokenRequestSerializer,
    ServiceUserAuthInvalidateRequestSerializer,
    TimedAuthTokenPairSerializer,
    TokenCreateRequestSerializer,
    VerifyTokenRequestSerializer,
)
from users.utils.auth import AuthManager


class AuthViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        request_body=TokenCreateRequestSerializer,
        responses={status.HTTP_200_OK: TimedAuthTokenPairSerializer},
        tags=["auth"],
    )
    @action(methods=["POST"], detail=False, url_path="token", url_name="token")
    def token_create(self, request: Request):
        serializer = TokenCreateRequestSerializer(data=request.data)
        _ = serializer.is_valid(raise_exception=True)

        validated_data = cast(dict[str, Any], serializer.validated_data)
        hq_token = validated_data.get("hq_token", "")

        user_data = AuthManager.verify_hq_token(hq_token)

        email = user_data.get("email", "")
        user = User.objects.filter(email=email).first()

        if user is None:
            user = User.objects.create_user(
                email=email, password=base64.urlsafe_b64encode(os.urandom(15)).decode()
            )
        user.hq_user_data = user_data
        user.save()

        token = TimedAuthTokenPair.create_for_user(user)

        return Response(
            TimedAuthTokenPairSerializer(token).data, status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        request_body=VerifyTokenRequestSerializer,
        responses={status.HTTP_200_OK: TimedAuthTokenPairSerializer},
        tags=["auth"],
    )
    @action(methods=["POST"], detail=False, url_path="verify", url_name="verify")
    def verify(self, request: Request):
        serializer = VerifyTokenRequestSerializer(data=request.data)
        _ = serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        token = get_object_or_404(TimedAuthTokenPair, token=validated_data.get("token"))

        try:
            jwt.decode(token.token, cast(str, settings.SECRET_KEY), algorithms=["H256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token Expired")

        return Response(
            TimedAuthTokenPairSerializer(token).data, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        request_body=RefreshTokenRequestSerializer,
        responses={status.HTTP_200_OK: TimedAuthTokenPairSerializer},
        tags=["auth"],
    )
    @action(methods=["POST"], detail=False, url_path="refresh", url_name="refresh")
    def refresh_token(self, request: Request):
        serializer = RefreshTokenRequestSerializer(data=request.data)
        _ = serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        token = get_object_or_404(
            TimedAuthTokenPair, refresh_token=validated_data.get("refresh_token")
        )

        if timezone.now() > token.expires_at:
            _ = token.delete()
            raise exceptions.AuthenticationFailed("Refresh Token Expired")

        new_token = TimedAuthTokenPair.create_for_user(token.user)
        _ = token.delete()

        return Response(
            TimedAuthTokenPairSerializer(new_token).data, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        request_body=ServiceUserAuthInvalidateRequestSerializer,
        responses={status.HTTP_200_OK: MessageResponseSerializer},
        tags=["auth"],
    )
    @action(
        methods=["POST"],
        detail=False,
        url_path="service_user_auth_invalidate",
        url_name="service-user-auth-invalidate",
        permission_classes=[BaseAuthServicePermissions],
    )
    def service_user_auth_invalidate(self, request: Request):
        serializer = ServiceUserAuthInvalidateRequestSerializer(data=request.data)
        _ = serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        user = User.objects.filter(
            hq_user_data__id=validated_data.get("hq_user_id")
        ).first()

        if user is None:
            raise exceptions.NotFound("User not found")

        _ = TimedAuthTokenPair.objects.filter(user=user).delete()

        return Response(
            MessageResponseSerializer(data={"message": "User Authentication Revoked"}),
            status=status.HTTP_200_OK,
        )
