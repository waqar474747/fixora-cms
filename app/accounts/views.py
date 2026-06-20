# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.views.decorators.csrf import csrf_protect  # <-- make sure this is here

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import UserProfile, ActivityLog

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(user, action_type, description='', request=None):
    """Log user activity"""
    if user and user.is_authenticated:
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

        ActivityLog.objects.create(
            user=user,
            action_type=action_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )


@require_http_methods(["POST", "GET"])
def logout_view(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            log_activity(request.user, 'LOGOUT', 'User logged out', request)
            logout(request)
            messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')

    if request.user.is_authenticated:
        log_activity(request.user, 'LOGOUT', 'User logged out', request)
        logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@csrf_protect
def register(request):
    if request.user.is_authenticated:
        try:
            p = request.user.profile
        except:
            p = UserProfile.objects.create(user=request.user)
        if p.is_admin() or request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:user_dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user, 'PROFILE_UPDATE', 'User registered', request)
            messages.success(request, 'Registration successful! You can now login with your credentials.')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        try:
            p = request.user.profile
        except:
            p = UserProfile.objects.create(user=request.user)
        if p.is_admin() or request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:user_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username_or_email')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')

            user = authenticate(request, username=username_or_email, password=password)

            if not user:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user:
                login(request, user)

                if remember_me:
                    request.session.set_expiry(1209600)
                else:
                    request.session.set_expiry(0)

                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.last_login_ip = get_client_ip(request)
                profile.save()

                log_activity(user, 'LOGIN', 'User logged in', request)

                if profile.is_admin() or user.is_staff or user.is_superuser:
                    default_redirect = 'dashboard:admin_dashboard'
                elif profile.is_staff_member():
                    default_redirect = 'dashboard:staff_dashboard'
                else:
                    default_redirect = 'dashboard:user_dashboard'

                next_url = request.GET.get('next', default_redirect)
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required(login_url='accounts:login')
def profile(request):
    """User profile edit view"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile, user=request.user)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.email = form.cleaned_data.get('email')
            user.save()
            form.save()

            log_activity(request.user, 'PROFILE_UPDATE', 'User updated profile', request)
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user_profile, user=request.user)

    context = {
        'form': form,
        'user_profile': user_profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='accounts:login')
def profile_view(request):
    """View user profile (read-only)"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'user_profile': user_profile,
    }
    return render(request, 'accounts/profile_view.html', context)


@csrf_protect
def admin_login_view(request):
    if request.user.is_authenticated:
        try:
            p = request.user.profile
        except:
            p = UserProfile.objects.create(user=request.user)
        if p.is_admin() or request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:user_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username_or_email')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username_or_email, password=password)
            if not user:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user:
                profile = UserProfile.objects.filter(user=user).first()
                if profile and profile.is_admin():
                    login(request, user)
                    profile.last_login_ip = get_client_ip(request)
                    profile.save()
                    log_activity(user, 'LOGIN', 'Admin logged in', request)
                    return redirect('dashboard:admin_dashboard')
                else:
                    messages.error(request, 'Access denied. Admin privileges required.')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/admin_login.html', {'form': form})


@login_required(login_url='accounts:login')
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activity(request.user, 'PROFILE_UPDATE', 'Password changed', request)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


def home_redirect(request):
    if request.user.is_authenticated:
        try:
            p = request.user.profile
        except:
            p = UserProfile.objects.create(user=request.user)
        if p.is_admin() or request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        return redirect('dashboard:user_dashboard')
    return redirect('accounts:login')
