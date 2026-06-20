from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import status, generics, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from app.complaints.models import Complaint, Category, Department, ComplaintHistory, Notification, ComplaintFeedback
from app.accounts.models import UserProfile, ActivityLog
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    CategorySerializer, DepartmentSerializer,
    ComplaintListSerializer, ComplaintCreateSerializer,
    ComplaintStatusUpdateSerializer, ComplaintHistorySerializer,
    NotificationSerializer, ComplaintFeedbackSerializer,
    UserProfileSerializer, DashboardStatsSerializer
)
from .permissions import IsAdminUser, IsAdminOrStaffUser


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.get(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        UserProfile.objects.get_or_create(user=user)
        profile = user.profile
        django_login(request, user)
        ActivityLog.objects.create(
            user=user, action_type='LOGIN',
            description='User logged in via API'
        )
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_view(request):
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        ActivityLog.objects.create(
            user=request.user, action_type='LOGOUT',
            description='User logged out via API'
        )
        return Response({'message': 'Logged out successfully.'})
    except Token.DoesNotExist:
        return Response({'message': 'Already logged out.'})


@api_view(['GET'])
def user_profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return Response(UserProfileSerializer(profile).data)


@api_view(['PUT', 'PATCH'])
def update_profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user = request.user
    data = request.data

    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    user.save()

    serializer = UserProfileSerializer(profile, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        ActivityLog.objects.create(
            user=user, action_type='PROFILE_UPDATE',
            description='User updated profile via API'
        )
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class ComplaintListCreateView(generics.ListCreateAPIView):
    serializer_class = ComplaintListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            profile = self.request.user.profile
            if profile.is_admin():
                return Complaint.objects.all()
            if profile.is_staff_member() and profile.department:
                return Complaint.objects.filter(department=profile.department)
        except:
            pass
        return Complaint.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ComplaintCreateSerializer
        return ComplaintListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        complaint = serializer.instance
        Notification.objects.create(
            user=self.request.user,
            complaint=complaint,
            notification_type='SUBMISSION',
            title='Complaint Submitted',
            message=f'Your complaint "{complaint.title}" has been submitted successfully.'
        )
        ActivityLog.objects.create(
            user=self.request.user, action_type='COMPLAINT_SUBMIT',
            description=f'Submitted complaint {complaint.complaint_id}'
        )


class ComplaintDetailView(generics.RetrieveAPIView):
    serializer_class = ComplaintListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            profile = self.request.user.profile
            if profile.is_admin():
                return Complaint.objects.all()
            if profile.is_staff_member() and profile.department:
                return Complaint.objects.filter(department=profile.department)
        except:
            pass
        return Complaint.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ActivityLog.objects.create(
            user=request.user, action_type='COMPLAINT_VIEW',
            description=f'Viewed complaint {instance.complaint_id}'
        )
        serializer = self.get_serializer(instance)
        history = ComplaintHistory.objects.filter(complaint=instance)
        history_serializer = ComplaintHistorySerializer(history, many=True)
        data = serializer.data
        data['history'] = history_serializer.data
        return Response(data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_complaint_status_view(request, pk):
    try:
        profile = request.user.profile
        if not profile.is_admin() and not profile.is_staff_member():
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    except:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        complaint = Complaint.objects.get(pk=pk)
    except Complaint.DoesNotExist:
        return Response({'error': 'Complaint not found.'}, status=status.HTTP_404_NOT_FOUND)

    old_status = complaint.status
    serializer = ComplaintStatusUpdateSerializer(complaint, data=request.data, partial=True)
    if serializer.is_valid():
        updated = serializer.save()
        if updated.status == 'RESOLVED' and old_status != 'RESOLVED':
            updated.resolved_at = timezone.now()
            updated.save()

        ComplaintHistory.objects.create(
            complaint=complaint,
            changed_by=request.user,
            action=f'Status changed from {old_status} to {updated.status}',
            old_value=old_status,
            new_value=updated.status
        )
        Notification.objects.create(
            user=complaint.user,
            complaint=complaint,
            notification_type='STATUS_CHANGE',
            title='Complaint Status Updated',
            message=f'Your complaint status has been updated to {updated.get_status_display()}'
        )
        ActivityLog.objects.create(
            user=request.user, action_type='STATUS_CHANGE',
            description=f'Updated complaint {complaint.complaint_id} status'
        )
        return Response(ComplaintListSerializer(updated).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def track_complaint_view(request, tracking_id):
    """Public tracking - lookup complaint by tracking ID"""
    try:
        complaint = Complaint.objects.get(complaint_id=tracking_id.upper())
        serializer = ComplaintListSerializer(complaint)
        return Response(serializer.data)
    except Complaint.DoesNotExist:
        return Response({'error': 'Complaint not found with this tracking ID.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_complaints_view(request):
    query = request.query_params.get('q', '')
    status_filter = request.query_params.get('status', '')
    category_filter = request.query_params.get('category', '')
    priority_filter = request.query_params.get('priority', '')

    try:
        profile = request.user.profile
        if profile.is_admin():
            complaints = Complaint.objects.all()
        elif profile.is_staff_member() and profile.department:
            complaints = Complaint.objects.filter(department=profile.department)
        else:
            complaints = Complaint.objects.filter(user=request.user)
    except:
        complaints = Complaint.objects.filter(user=request.user)

    if query:
        complaints = complaints.filter(
            Q(complaint_id__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    if status_filter:
        complaints = complaints.filter(status=status_filter.upper())
    if category_filter:
        complaints = complaints.filter(category_id=category_filter)
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter.upper())

    complaints = complaints.order_by('-created_at')
    serializer = ComplaintListSerializer(complaints, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_view(request):
    user = request.user
    total = Complaint.objects.filter(user=user).count()
    submitted = Complaint.objects.filter(user=user, status='SUBMITTED').count()
    pending = Complaint.objects.filter(user=user, status='PENDING').count()
    under_review = Complaint.objects.filter(user=user, status='UNDER_REVIEW').count()
    in_progress = Complaint.objects.filter(user=user, status='IN_PROGRESS').count()
    resolved = Complaint.objects.filter(user=user, status='RESOLVED').count()
    rejected = Complaint.objects.filter(user=user, status='REJECTED').count()
    recent = Complaint.objects.filter(user=user).order_by('-created_at')[:5]
    unread_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]

    return Response({
        'total_complaints': total,
        'submitted_complaints': submitted,
        'pending_complaints': pending,
        'under_review_complaints': under_review,
        'in_progress_complaints': in_progress,
        'resolved_complaints': resolved,
        'rejected_complaints': rejected,
        'recent_complaints': ComplaintListSerializer(recent, many=True).data,
        'unread_notifications': NotificationSerializer(unread_notifications, many=True).data,
        'status_data': [
            {'status': 'Submitted', 'count': submitted, 'color': '#6C757D'},
            {'status': 'Pending', 'count': pending, 'color': '#FFC107'},
            {'status': 'Under Review', 'count': under_review, 'color': '#17A2B8'},
            {'status': 'In Progress', 'count': in_progress, 'color': '#0D6EFD'},
            {'status': 'Resolved', 'count': resolved, 'color': '#28A745'},
            {'status': 'Rejected', 'count': rejected, 'color': '#DC3545'},
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_view(request):
    try:
        profile = request.user.profile
        if not profile.is_admin():
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    except:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    last_7_days = timezone.now() - timedelta(days=7)
    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status='PENDING').count()
    in_progress = Complaint.objects.filter(status='IN_PROGRESS').count()
    resolved = Complaint.objects.filter(status='RESOLVED').count()
    rejected = Complaint.objects.filter(status='REJECTED').count()
    total_users = User.objects.count()
    complaints_last_7_days = Complaint.objects.filter(created_at__gte=last_7_days).count()
    high_priority = Complaint.objects.filter(priority='HIGH', status__in=['PENDING', 'IN_PROGRESS']).count()
    recent = Complaint.objects.all().order_by('-created_at')[:10]

    category_data = Complaint.objects.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]

    return Response({
        'total_complaints': total,
        'pending_complaints': pending,
        'in_progress_complaints': in_progress,
        'resolved_complaints': resolved,
        'rejected_complaints': rejected,
        'total_users': total_users,
        'complaints_last_7_days': complaints_last_7_days,
        'high_priority_complaints': high_priority,
        'recent_complaints': ComplaintListSerializer(recent, many=True).data,
        'status_data': [
            {'status': 'Pending', 'count': pending, 'color': '#FFC107'},
            {'status': 'In Progress', 'count': in_progress, 'color': '#17A2B8'},
            {'status': 'Resolved', 'count': resolved, 'color': '#28A745'},
            {'status': 'Rejected', 'count': rejected, 'color': '#DC3545'},
        ],
        'category_data': list(category_data),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read_view(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read.'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All notifications marked as read.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback_view(request, pk):
    try:
        complaint = Complaint.objects.get(pk=pk)
    except Complaint.DoesNotExist:
        return Response({'error': 'Complaint not found.'}, status=status.HTTP_404_NOT_FOUND)

    if complaint.user != request.user:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if complaint.status != 'RESOLVED':
        return Response({'error': 'You can only rate resolved complaints.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ComplaintFeedbackSerializer(data=request.data)
    if serializer.is_valid():
        feedback, created = ComplaintFeedback.objects.get_or_create(complaint=complaint)
        feedback.rating = serializer.validated_data['rating']
        feedback.comment = serializer.validated_data.get('comment', '')
        feedback.save()
        return Response(ComplaintFeedbackSerializer(feedback).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_users_view(request):
    try:
        profile = request.user.profile
        if not profile.is_admin():
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    except:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.all()
    return Response(UserSerializer(users, many=True).data)
