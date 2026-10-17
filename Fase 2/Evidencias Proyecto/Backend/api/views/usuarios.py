from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.bitacora import registrar_en_bitacora
from api.models import Rol, Usuario
from api.permissions import EsAdministrador
from api.serializers import RolSerializer, UsuarioAdminSerializer


class RolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rol.objects.order_by("nombre")
    serializer_class = RolSerializer
    permission_classes = [EsAdministrador]


class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioAdminSerializer
    permission_classes = [EsAdministrador]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        usuarios = Usuario.objects.select_related("rol").order_by("nombre")
        parametros = self.request.query_params

        buscar = parametros.get("buscar", "").strip()
        if buscar:
            usuarios = usuarios.filter(Q(nombre__icontains=buscar) | Q(email__icontains=buscar))

        activo = parametros.get("activo")
        if activo in ("true", "false"):
            usuarios = usuarios.filter(is_active=activo == "true")

        rol = parametros.get("rol")
        if rol and rol.isdigit():
            usuarios = usuarios.filter(rol_id=rol)

        return usuarios

    def perform_create(self, serializer):
        usuario = serializer.save()
        registrar_en_bitacora(
            self.request,
            "USUARIO_CREADO",
            self.request.user,
            entidad_id=usuario.id,
            detalle={"email": usuario.email, "rol": usuario.rol.nombre},
        )

    def perform_update(self, serializer):
        usuario = serializer.instance
        cambios = serializer.validated_data

        # Evita que un administrador se quede sin acceso por error.
        if usuario == self.request.user:
            if cambios.get("is_active") is False:
                raise ValidationError("No puedes desactivar tu propia cuenta.")
            if "rol" in cambios and cambios["rol"] != usuario.rol:
                raise ValidationError("No puedes cambiar tu propio rol.")

        campos_modificados = sorted("activo" if campo == "is_active" else campo for campo in cambios)
        usuario = serializer.save()

        if not usuario.is_active or "password" in cambios:
            Token.objects.filter(user=usuario).delete()

        registrar_en_bitacora(
            self.request,
            "USUARIO_EDITADO",
            self.request.user,
            entidad_id=usuario.id,
            detalle={"campos": campos_modificados},
        )

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()

        if usuario == request.user:
            raise ValidationError("No puedes desactivar tu propia cuenta.")

        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        Token.objects.filter(user=usuario).delete()
        registrar_en_bitacora(request, "USUARIO_DESACTIVADO", request.user, entidad_id=usuario.id)

        return Response(status=status.HTTP_204_NO_CONTENT)
