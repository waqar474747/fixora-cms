from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.is_admin()
        except:
            return request.user.is_superuser


class IsAdminOrStaffUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            profile = request.user.profile
            return profile.is_admin() or profile.is_staff_member()
        except:
            return request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
