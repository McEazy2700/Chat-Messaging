from django.db.models import Exists, OuterRef
from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method

from messaging.models.chat import (
    ChatRoom,
    ChatRoomMember,
    ChatRoomMessage,
    ChatRoomMessageReadReciepts,
    ChatRoomType,
)
from users.serializers.user import UserSerializer


class ChatRoomMemberDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(allow_null=True, required=False)

    class Meta:
        model = ChatRoomMember
        fields = ["id", "date_added", "active", "user"]


class ChatRoomMessageDetailSerializer(serializers.ModelSerializer):
    edited = serializers.SerializerMethodField()
    sender = ChatRoomMemberDetailSerializer()

    class Meta:
        model = ChatRoomMessage
        fields = [
            "id",
            "text",
            "url",
            "url_content_type",
            "date_added",
            "edited",
            "sender",
        ]

    @swagger_serializer_method(
        serializer_or_field=serializers.BooleanField(allow_null=True)
    )
    def get_edited(self, message: ChatRoomMessage):
        return message.date_added != message.last_updated


class ChatRoomMessageRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoomMessage
        fields = ["text", "url", "url_content_type"]


class ChatRoomCreateRequestSerializer(serializers.ModelSerializer):
    pair_email = serializers.EmailField(allow_null=True, required=False)

    class Meta:
        model = ChatRoom
        fields = ["name", "cover_image_url", "type", "pair_email"]


class ChatRoomEditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ["name", "cover_image_url", "type"]


class ChatRoomDetailsSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "cover_image_url",
            "type",
            "date_added",
            "display_name",
            "unread",
        ]

    @swagger_serializer_method(
        serializer_or_field=serializers.CharField(allow_null=True)
    )
    def get_display_name(self, room: ChatRoom):
        if room.type == ChatRoomType.Pair:
            request = self.context.get("request")

            if request and hasattr(request, "user"):
                reciever_member = (
                    ChatRoomMember.objects.select_related("user__profile")
                    .filter(chat_room=room)
                    .exclude(user=request.user)
                    .first()
                )
                if reciever_member:
                    return (
                        reciever_member.user.profile.full_name
                        if hasattr(reciever_member.user, "profile")
                        else reciever_member.user.email
                    )

        return room.name

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField())
    def get_unread(self, chat_room: ChatRoom):
        request = self.context.get("request")

        if request and hasattr(request, "user"):
            member = ChatRoomMember.objects.get(chat_room=chat_room, user=request.user)
            return (
                ChatRoomMessage.objects.filter(chat_room=chat_room)
                .exclude(sender=member)
                .filter(
                    ~Exists(
                        ChatRoomMessageReadReciepts.objects.filter(
                            message=OuterRef("id"), member=member
                        )
                    )
                )
            ).count()

        return 0


class ChatRoomAddMemeberRequestSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
