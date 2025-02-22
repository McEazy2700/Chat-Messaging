from django.urls import include, path
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from messaging.views.chat import (
    ChatRoomMembersViewSet,
    ChatRoomMessageViewSet,
    ChatRoomViewSet,
)

router = routers.DefaultRouter()
router.register(r"chat", ChatRoomViewSet, basename="chat")
nested_router = NestedSimpleRouter(router, r"chat", lookup="chat")
nested_router.register(r"members", ChatRoomMembersViewSet, basename="members")
nested_router.register(r"messages", ChatRoomMessageViewSet, basename="messages")

urlpatterns = [path(r"", include(router.urls)), path(r"", include(nested_router.urls))]
