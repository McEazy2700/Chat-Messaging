from datetime import timedelta
from typing import Any, cast
import uuid
import jwt
import secrets
from django.db import models
from django.utils import timezone
from django.conf import settings

from users.models.users import User


class TimedAuthTokenPair(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=500, unique=True)
    refresh_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @classmethod
    def create_for_user(cls, user: User):
        auth_settings = cast(dict[str, Any], settings.CUSTOM_AUTH)
        encoded = jwt.encode(
            {
                "email": user.email,
                "iat": timezone.now(),
                "exp": timezone.now()
                + timedelta(hours=auth_settings.get("TOKEN_VALID_DURATION_HOURS") or 2),
            },
            cast(str, settings.SECRET_KEY),
        )
        refresh_token = secrets.token_hex(32)
        return TimedAuthTokenPair.objects.create(
            user=user,
            token=encoded,
            refresh_token=refresh_token,
            expires_at=timezone.now()
            + timedelta(
                hours=auth_settings.get("REFRESH_TOKEN_VALID_DURATION_HOURS") or 2
            ),
        )
