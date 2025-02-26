from typing import Any, Optional, cast
from asgiref.sync import async_to_sync
from channels.layers import BaseChannelLayer, get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.generics import mixins
from rest_framework.views import Request, Response, exceptions, status
from drf_yasg.utils import swagger_auto_schema

from messaging.filters.chat import ChatRoomMessageFilter
from messaging.models.chat import (
    ChatRoom,
    ChatRoomMember,
    ChatRoomMessage,
    ChatRoomMessageReadReciepts,
)
from messaging.pagination.chat import ChatMessagesPagination
from messaging.permissions.chat import (
    CanEditMessagePermission,
    CanSendMessagePermission,
    CanViewMessagePermission,
)
from messaging.serializers.chat import (
    ChatRoomAddMemeberRequestSerializer,
    ChatRoomCreateRequestSerializer,
    ChatRoomEditRequestSerializer,
    ChatRoomMemberDetailSerializer,
    ChatRoomMessageDetailSerializer,
    ChatRoomMessageRequestSerializer,
    ChatRoomDetailsSerializer,
)

User = get_user_model()


class ChatRoomMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatRoomMessage.objects.all().order_by("date_added")
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomMessageDetailSerializer
    pagination_class = ChatMessagesPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ChatRoomMessageFilter
    search_fields = ["text"]

    def get_queryset(self):
        return self.queryset.filter(chat_room__pk=self.kwargs.get("chat_pk"))

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ChatRoomMessageRequestSerializer
        return ChatRoomMessageDetailSerializer

    def get_permissions(self):
        permission_classes = []
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated, CanSendMessagePermission]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [permissions.IsAuthenticated, CanEditMessagePermission]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated, CanViewMessagePermission]

        return [permission() for permission in permission_classes]

    def destroy(self, request: Request, *args: Any, **kwargs: Any):
        message = cast(ChatRoomMessage, self.get_object())
        if message.sender != request.user:  # pyright: ignore[reportUnreachable]
            raise exceptions.PermissionDenied(
                "You do not have permission to delete this message."
            )  # pyright: ignore[reportUnreachable]

        channel_layer = cast(BaseChannelLayer, get_channel_layer())
        group_name = f"chat_{self.kwargs.get('chat_pk')}"
        async_to_sync(channel_layer.group_send)(
            group_name, {"type": "chat_message_delete", "data": str(message.id)}
        )

        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ChatRoomMessageRequestSerializer,
        responses={
            status.HTTP_201_CREATED: ChatRoomMessageDetailSerializer,
        },
        operation_summary="Send Message",
        operation_description="Sends a message to a specified chat room.",
    )
    def create(self, request: Request, *args: Any, **kwargs: Any):
        request_serializer = cast(
            ChatRoomMessageRequestSerializer,
            ChatRoomMessageRequestSerializer(data=request.data),
        )
        _ = request_serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], request_serializer.validated_data)

        chat_room_id = self.kwargs.get("chat_pk")
        chat_room = get_object_or_404(ChatRoom, pk=chat_room_id)

        sender = ChatRoomMember.objects.filter(
            chat_room=chat_room, user=request.user
        ).first()

        message = ChatRoomMessage.objects.create(
            **validated_data, chat_room=chat_room, sender=sender
        )

        read_receipts = [
            ChatRoomMessageReadReciepts(message=message, member=member)
            for member in ChatRoomMember.objects.filter(
                chat_room=chat_room, online=True, active=True
            )
        ]
        _ = ChatRoomMessageReadReciepts.objects.bulk_create(read_receipts)

        response_serializer = ChatRoomMessageDetailSerializer(message)

        channel_layer = cast(BaseChannelLayer, get_channel_layer())
        group_name = f"chat_{chat_room_id}"
        async_to_sync(channel_layer.group_send)(
            group_name, {"type": "chat_message", "data": response_serializer.data}
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        request_body=ChatRoomMessageRequestSerializer,
        responses={
            status.HTTP_200_OK: ChatRoomMessageDetailSerializer,
        },
        operation_summary="Edit message",
        operation_description="Edit certain information of chat message.",
    )
    def update(self, request: Request, *args: Any, **kwargs: Any):
        request_serializer = cast(
            ChatRoomMessageRequestSerializer,
            ChatRoomMessageRequestSerializer(data=request.data),
        )
        _ = request_serializer.is_valid(raise_exception=True)

        message = cast(ChatRoomMessage, self.get_object())
        if message.sender != self.request.user:  # pyright: ignore[reportUnreachable]
            return exceptions.PermissionDenied(
                "You do not have permission to edit this message."
            )  # pyright: ignore[reportUnreachable]

        message = request_serializer.save()
        response_serializer = ChatRoomMessageDetailSerializer(message)

        channel_layer = cast(BaseChannelLayer, get_channel_layer())
        group_name = f"chat_{self.kwargs.get('chat_pk')}"
        async_to_sync(channel_layer.group_send)(
            group_name, {"type": "chat_message_edit", "data": response_serializer.data}
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomDetailsSerializer
    queryset = ChatRoom.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ChatRoomCreateRequestSerializer
        elif self.action in ["update", "partial_update"]:
            return ChatRoomEditRequestSerializer
        return ChatRoomDetailsSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(chatroommember__user=self.request.user)
        return self.queryset

    def perform_update(self, serializer: ChatRoomEditRequestSerializer):
        chat_room = cast(ChatRoom, self.get_object())
        if (
            chat_room.created_by != self.request.user
        ):  # pyright: ignore[reportUnreachable]
            return exceptions.PermissionDenied(
                "You do not have permission to update this chat room."
            )  # pyright: ignore[reportUnreachable]
        return super().perform_update(serializer)

    def destroy(self, request: Request, *args: Any, **kwargs: Any):
        chat_room = cast(ChatRoom, self.get_object())
        if chat_room.created_by != request.user:  # pyright: ignore[reportUnreachable]
            raise exceptions.PermissionDenied(
                "You do not have permission to delete this chat room."
            )  # pyright: ignore[reportUnreachable]

        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ChatRoomCreateRequestSerializer,
        responses={
            status.HTTP_201_CREATED: ChatRoomDetailsSerializer,
        },
        operation_summary="Create chat room",
        operation_description="Creates a new chat room with the provided data.",
    )
    def create(self, request: Request, *args: Any, **kwargs: Any):
        request_serializer = cast(
            ChatRoomCreateRequestSerializer,
            ChatRoomCreateRequestSerializer(data=request.data),
        )
        _ = request_serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], request_serializer.validated_data)
        pair_email = validated_data.pop("pair_email")
        pair_user = get_object_or_404(User, email=pair_email)

        chat_room = ChatRoom.objects.create(**validated_data)
        _ = ChatRoomMember.objects.create(user=self.request.user, chat_room=chat_room)
        _ = ChatRoomMember.objects.create(user=pair_user, chat_room=chat_room)

        response_serializer = ChatRoomDetailsSerializer(request_serializer.instance)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        request_body=ChatRoomEditRequestSerializer,
        responses={
            status.HTTP_200_OK: ChatRoomDetailsSerializer,
        },
        operation_summary="Update chat room",
        operation_description="Edit certain information of a chat room",
    )
    def update(self, request: Request, *args: Any, **kwargs: Any):
        request_serializer = cast(
            ChatRoomEditRequestSerializer,
            ChatRoomEditRequestSerializer(data=request.data),
        )
        _ = request_serializer.is_valid(raise_exception=True)
        _ = self.perform_update(request_serializer)

        response_serializer = ChatRoomDetailsSerializer(
            request_serializer.instance
        )  # pyright: ignore[reportUnreachable]

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        request_body=None,
        responses={status.HTTP_200_OK: None},
        operation_summary="Clear Unread",
        operation_description="Clears a users unread messages",
    )
    @action(
        methods=["DELETE"],
        detail=True,
        url_path="clear_unread",
        url_name="clear-unread",
    )
    def clear_unread(self, request: Request, pk: Optional[str] = None):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        member = ChatRoomMember.objects.get(chat_room=chat_room, user=request.user)

        unread_messages = (
            ChatRoomMessage.objects.filter(chat_room=chat_room)
            .exclude(sender=member)
            .filter(
                ~Exists(
                    ChatRoomMessageReadReciepts.objects.filter(
                        message=OuterRef("id"), member=member
                    )
                )
            )
        )

        read_receipts = [
            ChatRoomMessageReadReciepts(message=message, member=member)
            for message in unread_messages
        ]

        _ = ChatRoomMessageReadReciepts.objects.bulk_create(read_receipts)

        channel_layer = cast(BaseChannelLayer, get_channel_layer())
        group_name = f"chat_{self.kwargs.get('chat_pk')}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {"type": "clear_unread", "data": str(self.kwargs.get("chat_pk"))},
        )

        return Response(
            None,
            status=status.HTTP_200_OK,
        )


class ChatRoomMembersViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ChatRoomMember.objects.all()
    serializer_class = ChatRoomMemberDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChatRoomAddMemeberRequestSerializer,
        responses={
            status.HTTP_201_CREATED: ChatRoomMemberDetailSerializer,
        },
    )
    def create(self, request: Request, *args: Any, **kwargs: Any):
        serializer = ChatRoomAddMemeberRequestSerializer(data=request.data)
        _ = serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)

        user = get_object_or_404(User, email=validated_data.get("user_email"))
        room = cast(ChatRoom, self.get_object())
        room_member = ChatRoomMember.objects.get_or_create(
            chat_room=room, user=user
        )  # pyright: ignore[reportUnreachable]

        response_serializer = ChatRoomMemberDetailSerializer(room_member)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
