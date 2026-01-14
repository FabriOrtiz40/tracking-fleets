from rest_framework import permissions


class IsOrganizationMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            if hasattr(request.user, 'driver_profile'):
                return obj.organization == request.user.driver_profile.organization
        return False


class IsVehicleDriver(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'driver_profile'):
            if hasattr(obj, 'current_driver'):
                return obj.current_driver == request.user.driver_profile
        return False


class IsDriverOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'driver_profile')
