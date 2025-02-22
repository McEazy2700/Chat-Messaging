from django.urls import include, path
from rest_framework import routers

from users.views.auth import AuthViewSet

router = routers.DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = [path("", include(router.urls))]
