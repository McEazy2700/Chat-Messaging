from typing import TYPE_CHECKING
from rest_framework import permissions
from rest_framework.views import Request
from rest_framework.viewsets import ViewSet

from messaging.models.chat import ChatRoomMember

if TYPE_CHECKING:
    from users.models.users import User


class CanSendMessagePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet):
        user: User = request.user

        if not user.is_authenticated:
            return False

        chat_room_id = view.kwargs.get("chat_pk")
        if chat_room_id:
            member = ChatRoomMember.objects.filter(
                chat_room__id=chat_room_id, user=user
            ).first()

            if not member or not member.active:
                return False

        return "can_send_message" in user.hq_user_data["permissions"]


class CanEditMessagePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet):
        user: User = request.user

        if not user.is_authenticated:
            return False

        return "can_edit_message" in user.hq_user_data["permissions"]


class CanViewMessagePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet):
        user: User = request.user

        if not user.is_authenticated:
            return False

        chat_room_id = view.kwargs.get("chat_pk")
        if chat_room_id:
            member_exists = ChatRoomMember.objects.filter(
                chat_room__id=chat_room_id, user=user
            ).exists()

            if not member_exists:
                return False

        return "can_view_chat" in user.hq_user_data["permissions"]
