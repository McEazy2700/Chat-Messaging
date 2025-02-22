import uuid
from channels.auth import get_user_model
from django.db import models

User = get_user_model()


class ChatRoomType(models.TextChoices):
    Pair = "pair"
    GroupChat = "group_chat"


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=255, null=True, blank=True)
    cover_image_url = models.CharField(max_length=500, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(
        max_length=40, choices=ChatRoomType.choices, default=ChatRoomType.Pair
    )
    date_added = models.DateTimeField(auto_now_add=True)


class ChatRoomMember(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)


class ChatRoomMessage(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.PROTECT)
    sender = models.ForeignKey(ChatRoomMember, on_delete=models.PROTECT)
    text = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=500, null=True, blank=True)
    url_content_type = models.CharField(max_length=255, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
