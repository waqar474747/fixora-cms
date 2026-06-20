from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from app.complaints.models import Complaint, Category, Department, ComplaintHistory, Notification, ComplaintFeedback
from app.accounts.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.get_or_create(user=user)
        Token.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label='Username or Email')
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if not user:
            raise serializers.ValidationError('Invalid username/email or password.')

        data['user'] = user
        return data


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'email', 'phone', 'description', 'is_active']


class ComplaintListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_color = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = ['id', 'complaint_id', 'title', 'description', 'category', 'category_name',
                  'department', 'department_name', 'status', 'status_display', 'status_color',
                  'priority', 'priority_display', 'user', 'user_name', 'is_anonymous',
                  'created_at', 'updated_at', 'resolved_at', 'admin_remarks',
                  'photo', 'document', 'qr_code_data', 'latitude', 'longitude', 'attachment']

    def get_status_color(self, obj):
        colors = {
            'SUBMITTED': 'secondary',
            'PENDING': 'warning',
            'UNDER_REVIEW': 'info',
            'IN_PROGRESS': 'primary',
            'RESOLVED': 'success',
            'REJECTED': 'danger',
        }
        return colors.get(obj.status, 'secondary')


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'department', 'priority', 'is_anonymous',
                  'attachment', 'photo', 'document', 'qr_code_data', 'latitude', 'longitude']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['status', 'admin_remarks', 'assigned_to']


class ComplaintHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True, allow_null=True)

    class Meta:
        model = ComplaintHistory
        fields = ['id', 'action', 'old_value', 'new_value', 'changed_by', 'changed_by_name', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    complaint_id_display = serializers.CharField(source='complaint.complaint_id', read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = ['id', 'complaint', 'complaint_id_display', 'notification_type', 'title', 'message', 'is_read', 'created_at']


class ComplaintFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintFeedback
        fields = ['id', 'rating', 'comment', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'role', 'phone', 'address', 'city', 'state', 'country', 'is_email_verified']


class DashboardStatsSerializer(serializers.Serializer):
    total_complaints = serializers.IntegerField()
    pending_complaints = serializers.IntegerField()
    in_progress_complaints = serializers.IntegerField()
    resolved_complaints = serializers.IntegerField()
    rejected_complaints = serializers.IntegerField()
    total_users = serializers.IntegerField()
    complaints_last_7_days = serializers.IntegerField()
    high_priority_complaints = serializers.IntegerField()
