from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Department, Complaint, ComplaintHistory, Notification, ComplaintFeedback


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['complaint_id', 'title', 'user', 'status_badge', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'category', 'department', 'created_at']
    search_fields = ['complaint_id', 'title', 'description', 'user__username']
    readonly_fields = ['complaint_id', 'created_at', 'updated_at', 'resolved_at']
    fieldsets = (
        ('Complaint Information', {
            'fields': ('complaint_id', 'user', 'title', 'description', 'category', 'department')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'is_anonymous')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Uploads', {
            'fields': ('attachment', 'photo', 'document'),
            'classes': ('collapse',)
        }),
        ('QR Code & Location', {
            'fields': ('qr_code_data', 'latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Admin Actions', {
            'fields': ('assigned_to', 'admin_remarks')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'SUBMITTED': '#6C757D',
            'PENDING': '#FFC107',
            'UNDER_REVIEW': '#17A2B8',
            'IN_PROGRESS': '#0D6EFD',
            'RESOLVED': '#28A745',
            'REJECTED': '#DC3545',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'action', 'changed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['complaint__complaint_id', 'action']
    readonly_fields = ['complaint', 'changed_by', 'action', 'old_value', 'new_value', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']


@admin.register(ComplaintFeedback)
class ComplaintFeedbackAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'rating_display', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['complaint__complaint_id', 'comment']
    readonly_fields = ['created_at']
    
    def rating_display(self, obj):
        return f"{obj.rating}/5 - {obj.get_rating_display()}"
    rating_display.short_description = 'Rating'
