# pyright: reportArgumentType = false, reportUnnecessaryComparison = false, reportIncompatibleVariableOverride = false
from typing import Any, Optional
import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as lz


class CustomUserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: dict[str, Any]
    ):
        if not email:
            raise ValueError(lz("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str, **extra_fields: dict[str, Any]
    ):
        _ = extra_fields.setdefault("is_staff", True)
        _ = extra_fields.setdefault("is_superuser", True)
        _ = extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(lz("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(lz("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    email = models.EmailField(unique=True, verbose_name=lz("email address"))
    hq_user_data = models.JSONField(default=dict[str, Any], null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: CustomUserManager = CustomUserManager()

    def __str__(self):
        return self.email

    def get_username(self):
        return self.email

    def get_short_name(self):
        return self.email.split("@")[0]

    def get_long_name(self):
        return self.email


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    other_names = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_image_url = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.username:
            return self.username
        return self.user.email
