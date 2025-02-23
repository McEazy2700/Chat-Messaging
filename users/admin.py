from django.contrib import admin

from users.models.auth import TimedAuthTokenPair

# Register your models here.

admin.site.register(TimedAuthTokenPair)
