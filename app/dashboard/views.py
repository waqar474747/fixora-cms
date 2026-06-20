from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from app.complaints.models import Complaint, Notification, Category, Department, ComplaintFeedback
from app.accounts.models import UserProfile


@login_required(login_url='accounts:login')
def dashboard(request):
    """Main dashboard view - dispatches by role"""
    try:
        user_profile = request.user.profile
    except:
        user_profile = UserProfile.objects.create(user=request.user)

    if user_profile.is_admin() or request.user.is_staff or request.user.is_superuser:
        return admin_dashboard(request)
    elif user_profile.is_staff_member():
        return staff_dashboard(request)
    else:
        return user_dashboard(request)


@login_required(login_url='accounts:login')
def admin_dashboard(request):
    """Admin dashboard with analytics - ADMIN ONLY"""
    try:
        user_profile = request.user.profile
    except:
        user_profile = UserProfile.objects.create(user=request.user)

    if not (user_profile.is_admin() or request.user.is_staff or request.user.is_superuser):
        if user_profile.is_staff_member():
            return redirect('dashboard:staff_dashboard')
        return redirect('dashboard:dashboard')

    total_users = User.objects.filter(is_active=True).count()
    total_complaints = Complaint.objects.count()
    submitted_complaints = Complaint.objects.filter(status='SUBMITTED').count()
    pending_complaints = Complaint.objects.filter(status='PENDING').count()
    under_review_complaints = Complaint.objects.filter(status='UNDER_REVIEW').count()
    in_progress_complaints = Complaint.objects.filter(status='IN_PROGRESS').count()
    resolved_complaints = Complaint.objects.filter(status='RESOLVED').count()
    rejected_complaints = Complaint.objects.filter(status='REJECTED').count()

    recent_complaints = Complaint.objects.all().order_by('-created_at')[:10]
    recent_activities = User.objects.filter(is_active=True).order_by('-date_joined')[:5]

    status_data = [
        {'status': 'Submitted', 'count': submitted_complaints, 'color': '#6C757D'},
        {'status': 'Pending', 'count': pending_complaints, 'color': '#FFC107'},
        {'status': 'Under Review', 'count': under_review_complaints, 'color': '#17A2B8'},
        {'status': 'In Progress', 'count': in_progress_complaints, 'color': '#0D6EFD'},
        {'status': 'Resolved', 'count': resolved_complaints, 'color': '#28A745'},
        {'status': 'Rejected', 'count': rejected_complaints, 'color': '#DC3545'},
    ]

    priority_data = [
        {'priority': 'Low', 'count': Complaint.objects.filter(priority='LOW').count()},
        {'priority': 'Medium', 'count': Complaint.objects.filter(priority='MEDIUM').count()},
        {'priority': 'High', 'count': Complaint.objects.filter(priority='HIGH').count()},
    ]

    category_data = Complaint.objects.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
    department_data = Department.objects.annotate(complaint_count=Count('complaint')).order_by('-complaint_count')[:5]

    last_7_days = timezone.now() - timedelta(days=7)
    complaints_last_7_days = Complaint.objects.filter(created_at__gte=last_7_days).count()
    high_priority_complaints = Complaint.objects.filter(priority='HIGH', status__in=['PENDING', 'IN_PROGRESS']).count()
    avg_resolution_time = Complaint.objects.filter(status='RESOLVED', resolved_at__isnull=False).extra(select={'avg_days': "AVG(julianday(resolved_at) - julianday(created_at))"}).first()

    context = {
        'total_users': total_users,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'rejected_complaints': rejected_complaints,
        'submitted_complaints': submitted_complaints,
        'under_review_complaints': under_review_complaints,
        'recent_complaints': recent_complaints,
        'recent_activities': recent_activities,
        'status_data': status_data,
        'priority_data': priority_data,
        'category_data': category_data,
        'department_data': department_data,
        'complaints_last_7_days': complaints_last_7_days,
        'high_priority_complaints': high_priority_complaints,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required(login_url='accounts:login')
def staff_dashboard(request):
    """Staff dashboard - sees department complaints only - STAFF ONLY"""
    try:
        user_profile = request.user.profile
    except:
        user_profile = UserProfile.objects.create(user=request.user)

    if not (user_profile.is_staff_member() or request.user.is_staff or request.user.is_superuser):
        if user_profile.is_admin():
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:dashboard')

    department = user_profile.department

    if not department:
        return user_dashboard(request)

    total_complaints = Complaint.objects.filter(department=department).count()
    pending_complaints = Complaint.objects.filter(department=department, status='PENDING').count()
    in_progress_complaints = Complaint.objects.filter(department=department, status='IN_PROGRESS').count()
    resolved_complaints = Complaint.objects.filter(department=department, status='RESOLVED').count()
    rejected_complaints = Complaint.objects.filter(department=department, status='REJECTED').count()
    submitted_complaints = Complaint.objects.filter(department=department, status='SUBMITTED').count()
    under_review_complaints = Complaint.objects.filter(department=department, status='UNDER_REVIEW').count()

    recent_complaints = Complaint.objects.filter(department=department).order_by('-created_at')[:10]

    status_data = [
        {'status': 'Pending', 'count': pending_complaints, 'color': '#FFC107'},
        {'status': 'In Progress', 'count': in_progress_complaints, 'color': '#17A2B8'},
        {'status': 'Resolved', 'count': resolved_complaints, 'color': '#28A745'},
        {'status': 'Rejected', 'count': rejected_complaints, 'color': '#DC3545'},
    ]

    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:5]

    context = {
        'total_complaints': total_complaints,
        'submitted_complaints': submitted_complaints,
        'under_review_complaints': under_review_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'rejected_complaints': rejected_complaints,
        'recent_complaints': recent_complaints,
        'department': department,
        'unread_notifications': unread_notifications,
        'status_data': status_data,
    }

    return render(request, 'dashboard/staff_dashboard.html', context)


@login_required(login_url='accounts:login')
def user_dashboard(request):
    """User dashboard - USER ONLY"""
    user = request.user
    try:
        user_profile = user.profile
    except:
        user_profile = UserProfile.objects.create(user=user)

    # Redirect admin/staff away from user dashboard
    if user_profile.is_admin() or user.is_staff or user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    if user_profile.is_staff_member():
        return redirect('dashboard:staff_dashboard')

    total_complaints = Complaint.objects.filter(user=user).count()
    submitted_complaints = Complaint.objects.filter(user=user, status='SUBMITTED').count()
    pending_complaints = Complaint.objects.filter(user=user, status='PENDING').count()
    under_review_complaints = Complaint.objects.filter(user=user, status='UNDER_REVIEW').count()
    in_progress_complaints = Complaint.objects.filter(user=user, status='IN_PROGRESS').count()
    resolved_complaints = Complaint.objects.filter(user=user, status='RESOLVED').count()
    rejected_complaints = Complaint.objects.filter(user=user, status='REJECTED').count()

    recent_complaints = Complaint.objects.filter(user=user).order_by('-created_at')[:5]
    unread_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]

    status_data = [
        {'status': 'Submitted', 'count': submitted_complaints, 'color': '#6C757D'},
        {'status': 'Pending', 'count': pending_complaints, 'color': '#FFC107'},
        {'status': 'Under Review', 'count': under_review_complaints, 'color': '#17A2B8'},
        {'status': 'In Progress', 'count': in_progress_complaints, 'color': '#0D6EFD'},
        {'status': 'Resolved', 'count': resolved_complaints, 'color': '#28A745'},
        {'status': 'Rejected', 'count': rejected_complaints, 'color': '#DC3545'},
    ]

    context = {
        'total_complaints': total_complaints,
        'submitted_complaints': submitted_complaints,
        'pending_complaints': pending_complaints,
        'under_review_complaints': under_review_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'rejected_complaints': rejected_complaints,
        'recent_complaints': recent_complaints,
        'unread_notifications': unread_notifications,
        'status_data': status_data,
    }

    return render(request, 'dashboard/user_dashboard.html', context)


@login_required(login_url='accounts:login')
def notifications(request):
    """View all notifications"""
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    # Mark as read
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)

    context = {
        'notifications': notifications,
    }

    return render(request, 'dashboard/notifications.html', context)


@login_required(login_url='accounts:login')
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = Notification.objects.get(pk=pk, user=request.user)
    notification.is_read = True
    notification.save()

    if notification.complaint:
        return redirect('complaints:detail', pk=notification.complaint.pk)
    else:
        return redirect('dashboard:notifications')


@login_required(login_url='accounts:login')
def mark_all_read(request):
    if request.method == "POST":
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

    return redirect('dashboard:notifications')


@login_required(login_url='accounts:login')
def reports(request):
    """Admin reports page - ADMIN ONLY"""
    try:
        user_profile = request.user.profile
    except:
        user_profile = UserProfile.objects.create(user=request.user)

    if not (user_profile.is_admin() or request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard:user_dashboard')

    total_users = User.objects.filter(is_active=True).count()
    total_complaints = Complaint.objects.count()
    resolved_complaints = Complaint.objects.filter(status='RESOLVED').count()
    pending_complaints = Complaint.objects.filter(status='PENDING').count()

    category_data = Complaint.objects.values('category__name').annotate(count=Count('id')).order_by('-count')
    department_data = Department.objects.annotate(complaint_count=Count('complaint')).order_by('-complaint_count')
    monthly_data = Complaint.objects.extra(select={'month': "strftime('%%m', created_at)", 'year': "strftime('%%Y', created_at)"}).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

    context = {
        'total_users': total_users,
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': pending_complaints,
        'category_data': category_data,
        'department_data': department_data,
        'monthly_data': monthly_data,
    }
    return render(request, 'dashboard/reports.html', context)