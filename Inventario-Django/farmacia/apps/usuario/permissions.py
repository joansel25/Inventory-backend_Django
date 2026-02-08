from rest_framework.permissions import BasePermission

class EsAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class EsFarmaceutico(BasePermission):
    """
    Permite acceso a admin y farmaceutico.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ['admin', 'farmaceutico']


class EsBodeguero(BasePermission):
    """
    Permite acceso a admin, farmaceutico y bodeguero.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ['admin', 'farmaceutico', 'bodeguero']

class EsAdminOEsFarmaceutico(BasePermission):
    """
    OR real entre admin y farmaceutico.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ['admin', 'farmaceutico']


class EsAdminOEsBodeguero(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ['admin', 'bodeguero']


class EsFarmaceuticoOEsBodeguero(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ['farmaceutico', 'bodeguero']
