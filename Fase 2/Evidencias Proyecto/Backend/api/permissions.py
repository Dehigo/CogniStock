from rest_framework.permissions import SAFE_METHODS, BasePermission

from api.models import Rol


class EsAdministrador(BasePermission):
    message = "Solo un administrador puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.rol.nombre == Rol.ADMINISTRADOR)


class PuedeGestionarInventario(BasePermission):
    message = "Solo el administrador o el encargado de inventario pueden hacer cambios."

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return usuario.rol.nombre in (Rol.ADMINISTRADOR, Rol.ENCARGADO)


class PuedeRegistrarSalidas(BasePermission):
    """Las salidas por QR las hacen los tres roles (HU-04, HU-05: el usuario operativo escanea y registra)."""

    message = "Tu rol no puede registrar salidas."

    def has_permission(self, request, view):
        usuario = request.user
        roles = (Rol.ADMINISTRADOR, Rol.ENCARGADO, Rol.OPERATIVO)
        return bool(usuario and usuario.is_authenticated and usuario.rol.nombre in roles)
