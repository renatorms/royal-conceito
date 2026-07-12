from rest_framework import permissions


class IsDonorOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.usuario or request.user.is_staff
