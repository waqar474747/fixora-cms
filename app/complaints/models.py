from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid

# Category Model
class Category(models.Model):
    """Complaint categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Department Model
class Department(models.Model):
    """Departments that handle complaints"""
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Priority Choices
PRIORITY_CHOICES = [
    ('LOW', 'Low'),
    ('MEDIUM', 'Medium'),
    ('HIGH', 'High'),
    ('EMERGENCY', 'Emergency'),
]

# Status Choices - Full workflow
STATUS_CHOICES = [
    ('SUBMITTED', 'Submitted'),
    ('PENDING', 'Pending'),
    ('UNDER_REVIEW', 'Under Review'),
    ('IN_PROGRESS', 'In Progress'),
    ('RESOLVED', 'Resolved'),
    ('REJECTED', 'Rejected'),
]


# Complaint Model
class Complaint(models.Model):
    """Main Complaint model"""
    # Basic Information
    complaint_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Additional Options
    is_anonymous = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # File Uploads
    attachment = models.FileField(
        upload_to='complaints/attachments/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx'])]
    )
    photo = models.ImageField(
        upload_to='complaints/photos/',
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    document = models.FileField(
        upload_to='complaints/documents/',
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    
    # QR Code & Location
    qr_code_data = models.CharField(max_length=500, blank=True, help_text='Data scanned from QR code')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Admin Remarks
    admin_remarks = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['complaint_id']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.complaint_id} - {self.title}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('complaints:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.complaint_id:
            # Generate unique FXR tracking ID
            year = timezone.now().strftime('%Y')
            last_today = Complaint.objects.filter(
                complaint_id__startswith=f'FXR-{year}-'
            ).order_by('-complaint_id').first()
            if last_today:
                last_num = int(last_today.complaint_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.complaint_id = f"FXR-{year}-{new_num:06d}"
        super().save(*args, **kwargs)
    
    def mark_resolved(self):
        """Mark complaint as resolved"""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.save()
    
    def get_status_display_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'SUBMITTED': 'secondary',
            'PENDING': 'warning',
            'UNDER_REVIEW': 'info',
            'IN_PROGRESS': 'primary',
            'RESOLVED': 'success',
            'REJECTED': 'danger',
        }
        return colors.get(self.status, 'secondary')


# Complaint History/Activity Log Model
class ComplaintHistory(models.Model):
    """Track changes to complaints"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Complaint Histories"
    
    def __str__(self):
        return f"{self.complaint.complaint_id} - {self.action}"


# Notification Model
class Notification(models.Model):
    """In-app notifications"""
    NOTIFICATION_TYPES = [
        ('SUBMISSION', 'Complaint Submitted'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('RESOLUTION', 'Complaint Resolved'),
        ('REJECTION', 'Complaint Rejected'),
        ('NEW_COMPLAINT', 'New Complaint Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


# Complaint Rating/Feedback Model
class ComplaintFeedback(models.Model):
    """User feedback on complaint resolution"""
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for {self.complaint.complaint_id}"
