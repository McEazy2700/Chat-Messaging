from django.contrib.auth import get_user_model
import jwt
from typing import Any, Optional, cast
from rest_framework.views import Request, exceptions
from rest_framework import authentication
from django.conf import settings

from users.models.auth import TimedAuthTokenPair

User = get_user_model()


class JWTAuthorization(authentication.BaseAuthentication):
    def authenticate(self, request: Request):
        authorization_key = cast(
            str, cast(dict[str, Any], settings.CUSTOM_AUTH).get("AUTH_HEADER_KEY", "")
        )
        authorization = cast(
            Optional[str], cast(dict[str, Any], request.META).get(authorization_key, {})
        )
        if not authorization:
            return None
        token = authorization.split(" ").pop()
        if not TimedAuthTokenPair.objects.filter(token=token).exists():
            return None
        try:
            email = cast(
                dict[str, Any],
                jwt.decode(token, cast(str, settings.SECRET_KEY), algorithms="HS256"),
            ).get("email")
            user = User.objects.filter(email=email).first()

            if user is None:
                raise exceptions.AuthenticationFailed("Invalid Token")

            return (user, None)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token Expired")

    def authenticate_header(self, request: Request):
        return cast(Any, 'Bearer realm="api"')
