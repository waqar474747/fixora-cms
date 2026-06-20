from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('reports/', views.reports, name='reports'),
    path('notifications/', views.notifications, name='notifications'),
    path(
        'notifications/mark-all-read/',
        views.mark_all_read,
        name='mark_all_read'
    ),
    path(
        'notifications/<int:pk>/read/',
        views.mark_notification_read,
        name='mark_read'
    ),
]
