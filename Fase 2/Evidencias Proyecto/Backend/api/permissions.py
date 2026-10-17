from rest_framework.permissions import BasePermission

from api.models import Rol


class EsAdministrador(BasePermission):
    message = "Solo un administrador puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.rol.nombre == Rol.ADMINISTRADOR)
