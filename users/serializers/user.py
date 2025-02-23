from rest_framework.schemas.coreapi import serializers
from drf_yasg.utils import swagger_serializer_method

from users.models.users import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "other_names",
            "bio",
            "phone_number",
            "profile_image_url",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    subscription_payment_paid = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "profile", "subscription_payment_paid"]

    @swagger_serializer_method(serializer_or_field=ProfileSerializer())
    def get_profile(self, user: User):
        profile = Profile.objects.filter(user=user).first()
        if profile:
            return ProfileSerializer(profile).data
        return None

    @swagger_serializer_method(
        serializer_or_field=serializers.BooleanField(allow_null=True)
    )
    def get_subscription_payment_paid(self, user: User):
        return user.hq_user_data["subscription_payment_paid"]
