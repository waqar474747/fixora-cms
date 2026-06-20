from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, ActivityLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ['role', 'phone', 'address', 'city', 'state', 'postal_code', 'country', 
              'is_email_verified', 'receive_email_notifications', 'dark_mode']
    readonly_fields = ['created_at', 'updated_at']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'city', 'is_email_verified', 'created_at']
    list_filter = ['role', 'is_email_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Email Verification', {
            'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('receive_email_notifications', 'receive_sms_notifications', 'dark_mode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login_ip'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'timestamp', 'ip_address']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['user', 'action_type', 'description', 'ip_address', 'user_agent', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
