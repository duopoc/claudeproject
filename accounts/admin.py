"""
Accounts admin configuration
"""
from django.contrib import admin
from .models import UserProfile, UserActivity


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'firstname', 'lastname', 'role', 'is_active_status', 'is_banned', 'mfa_enabled']
    list_filter = ['role', 'is_active_status', 'is_banned', 'gender', 'mfa_enabled']
    search_fields = ['user__username', 'firstname', 'lastname', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'firstname', 'lastname', 'gender', 'age', 'phone', 'profile_picture', 'nickname')
        }),
        ('Status & Role', {
            'fields': ('role', 'is_active_status', 'is_banned')
        }),
        ('MFA', {
            'fields': ('mfa_enabled', 'mfa_secret')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login_at')
        }),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
