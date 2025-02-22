import requests
from typing import Any, cast
from django.conf import settings
from rest_framework.views import exceptions


class AuthManager:
    @classmethod
    def verify_hq_token(cls, token: str) -> dict[str, Any]:
        auth_settings = cast(dict[str, Any], settings.CUSTOM_AUTH)
        url = f"{auth_settings.get('BASE_AUTH_SERVICE_URL')}{auth_settings.get('BASE_AUTH_SERVICE_VERIFICATION_ENDPOINT')}"
        data = {"token": token}

        headers = {
            "HTTP_X_SERVICE_API_KEY": f"{auth_settings.get('BASE_AUTH_ISSUED_SERVICE_NAME')} {auth_settings.get('BASE_AUTH_ISSUED_API_KEY')}"
        }
        response = requests.post(url, data, headers=headers)
        if response.status_code != 200:
            raise exceptions.AuthenticationFailed(response.json())

        return response.json()
