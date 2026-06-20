from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.utils import timezone

# Extended User Profile
class UserProfile(models.Model):
    """Extended user profile with additional information"""
    USER_ROLES = [
        ('USER', 'Regular User'),
        ('STAFF', 'Staff/Department Officer'),
        ('ADMIN', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES, default='USER')
    department = models.ForeignKey(
        'complaints.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='staff_members'
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Profile settings
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    receive_email_notifications = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_staff_member(self):
        return self.role == 'STAFF'
    
    def is_regular_user(self):
        return self.role == 'USER'


# Activity Log Model
class ActivityLog(models.Model):
    """Track user activities"""
    ACTION_TYPES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('COMPLAINT_SUBMIT', 'Complaint Submitted'),
        ('COMPLAINT_UPDATE', 'Complaint Updated'),
        ('COMPLAINT_VIEW', 'Complaint Viewed'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('PROFILE_UPDATE', 'Profile Updated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()}"
