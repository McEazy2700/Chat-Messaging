import django_filters

from messaging.models.chat import ChatRoom


class ChatRoomMessageFilter(django_filters.FilterSet):
    text = django_filters.CharFilter(lookup="icontains")

    class Meta:
        model = ChatRoom
        fields = ["text"]
