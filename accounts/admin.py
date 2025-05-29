# accounts/admin.py
from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_state', 'total_points')
    list_filter = ('current_state',)
    search_fields = ('user__username',)
    filter_horizontal = ('completed_challenges',)
