from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsSupervisorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['supervisor', 'admin']

class IsTecnicoOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return request.user.role in ['tecnico', 'supervisor', 'admin']  # Solo técnicos+ pueden escribir

class CanAssignOperario(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Solo supervisores y admin pueden asignar operarios
        return request.user.role in ['supervisor', 'admin']