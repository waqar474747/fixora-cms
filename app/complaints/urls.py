from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('submit/', views.submit_complaint, name='submit'),
    path('list/', views.complaint_list, name='list'),
    path('track/', views.track_complaint_page, name='track_page'),
    path('track/<str:tracking_id>/', views.complaint_track, name='track'),
    path('<int:pk>/', views.complaint_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_complaint, name='edit'),
    path('<int:pk>/delete/', views.delete_complaint, name='delete'),
    path('<int:pk>/update-status/', views.update_complaint_status, name='update_status'),
    path('<int:pk>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('<int:pk>/download-pdf/', views.download_complaint_pdf, name='download_pdf'),
]
