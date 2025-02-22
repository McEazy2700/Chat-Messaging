from typing import Any, Optional, cast
from rest_framework import permissions
from rest_framework.views import Request
from rest_framework.viewsets import ViewSet
from django.conf import settings


class BaseAuthServicePermissions(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet):
        api_key = cast(
            Optional[str],
            cast(dict[str, Any], request.META).get(
                "HTTP_X_BASE_AUTH_SERVICE_ISSUER_KEY"
            ),
        )

        if not api_key:
            return False

        auth_settings = cast(dict[str, Any], settings.CUSTOM_AUTH)

        return auth_settings.get("BASE_AUTH_ISSUED_ISSUER_KEY") == api_key
