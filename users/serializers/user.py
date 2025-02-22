from rest_framework.schemas.coreapi import serializers

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
    profile = ProfileSerializer(allow_null=True, required=False)

    class Meta:
        model = User
        fields = ["email", "profile"]

    def get_profile(self, user: User):
        profile = Profile.objects.filter(user=user).first()
        if profile:
            return ProfileSerializer(profile).data
        return None
