import json
from typing import Any, Optional, cast
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import BaseChannelLayer
from channels.sessions import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from messaging.models.chat import ChatRoomMember
from users.models.users import User


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args: Any, **kwargs: Any):
        self.user: AnonymousUser | User
        self.room_id: str
        self.room_group_name: str
        self.channel_layer: BaseChannelLayer
        super().__init__(*args, **kwargs)

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        if not "can_view_chat" in cast(User, self.user).hq_user_data["permissions"]:
            await self.close()
            return

        await self.set_online_status(True)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: str):
        await self.set_online_status(False)

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ):
        """
        When a message is received from WebSocket, send it to the chat room group.
        """
        if text_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": text_data,
                },
            )

    @database_sync_to_async
    def set_online_status(self, online: bool):
        try:
            chat_member = ChatRoomMember.objects.get(
                chat_room__id=self.room_id, user=self.user
            )
            print("===Before", self.user, self.room_id, chat_member.online)
            chat_member.online = online
            chat_member.save(update_fields=["online", "last_updated"])
            print("===After", self.user, self.room_id, chat_member.online)
        except ChatRoomMember.DoesNotExist:
            pass

    async def chat_message(self, event):
        """
        Handles incoming messages sent to the room group.
        """
        await self.send(text_data=json.dumps(event))

    async def clear_unread(self, event):
        await self.send(text_data=json.dumps(event))
