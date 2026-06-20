from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import path, include


def home_view(request):
    if request.user.is_authenticated:
        try:
            p = request.user.profile
        except:
            return redirect('accounts:login')
        if p.is_admin() or request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:user_dashboard')
    return redirect('accounts:login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('app.accounts.urls', namespace='accounts')),
    path('complaints/', include('app.complaints.urls', namespace='complaints')),
    path('dashboard/', include('app.dashboard.urls', namespace='dashboard')),
    path('api/', include('app.api.urls', namespace='api')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
