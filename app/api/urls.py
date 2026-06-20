from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile
    path('profile/', views.user_profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='profile_update'),

    # Categories & Departments
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('departments/', views.DepartmentListView.as_view(), name='departments'),

    # Complaints - search MUST come before <int:pk>
    path('complaints/search/', views.search_complaints_view, name='complaint_search'),
    path('complaints/track/<str:tracking_id>/', views.track_complaint_view, name='complaint_track'),
    path('complaints/', views.ComplaintListCreateView.as_view(), name='complaints'),
    path('complaints/<int:pk>/', views.ComplaintDetailView.as_view(), name='complaint_detail'),
    path('complaints/<int:pk>/status/', views.update_complaint_status_view, name='complaint_status'),
    path('complaints/<int:pk>/feedback/', views.submit_feedback_view, name='complaint_feedback'),

    # Dashboard
    path('dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read_view, name='notifications_read_all'),

    # Users
    path('users/', views.all_users_view, name='users'),
]
