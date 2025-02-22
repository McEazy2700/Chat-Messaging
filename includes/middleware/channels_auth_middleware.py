import jwt
import logging
from typing import Any, cast
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from users.models.users import User

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_authorization(authorization: str):
    token_name, token = authorization.split(None, 1)
    if token_name.lower() != "bearer":
        return AnonymousUser()
    try:
        decoded = cast(
            dict[str, Any], jwt.decode(token, cast(str, settings.SECRET_KEY), ["H256"])
        )
        user = User.objects.filter(email=decoded.get("email")).first()
        if not user:
            logger.warning("Token payload missing user email identifier.")
            return AnonymousUser()
        return user

    except jwt.ExpiredSignatureError:
        logger.warning("JWT signature expired")
        return AnonymousUser()


class TokenAuthMiddleWare:
    """
    Custom middleware to authenticate users based on a token in the WS_AUTHORIZATION header.
    (No changes needed in TokenAuthMiddleWare class itself, assuming you've already set it up)
    """

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any):
        headers = scope["headers"]

        if b"ws_authorization" in headers:
            try:
                authorization = headers[b"ws_authorization"]
                scope["user"] = get_user_from_authorization(str(authorization))
            except ValueError:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)


def TokenAuthMiddleWareStack(inner: Any):
    """
    Forces token auth directly on channels and then passes events down to the inner application.
    """
    return TokenAuthMiddleWare(inner)
