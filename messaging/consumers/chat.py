import json
from typing import Any, Optional, cast
from channels.generic.websocket import WebsocketConsumer
from channels.layers import BaseChannelLayer
from django.contrib.auth.models import AnonymousUser

from users.models.users import User


class ChatConsumer(WebsocketConsumer):
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
            self.close()
            return

        if not "can_view_chat" in cast(User, self.user).hq_user_data["permissions"]:
            self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.accept()

    async def disconnect(self, code: str):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ):
        pass
