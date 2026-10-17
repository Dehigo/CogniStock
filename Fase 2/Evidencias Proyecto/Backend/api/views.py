from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from api.models import BitacoraAuditoria, Rol, Usuario
from api.permissions import EsAdministrador
from api.serializers import LoginSerializer, RolSerializer, UsuarioAdminSerializer, UsuarioSerializer


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


def registrar_en_bitacora(request, accion, usuario=None, entidad="usuarios", entidad_id=None, detalle=None):
    BitacoraAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
        ip=request.META.get("REMOTE_ADDR"),
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


# Autenticación

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]

    usuario = authenticate(request, email=email, password=serializer.validated_data["password"])

    # El mismo mensaje para email inexistente, clave incorrecta o usuario inactivo,
    # así no se puede averiguar qué cuentas existen.
    if usuario is None:
        registrar_en_bitacora(request, "LOGIN_FALLIDO", detalle={"email": email})
        return Response(
            {"detail": "Email o contraseña incorrectos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token, _ = Token.objects.get_or_create(user=usuario)
    update_last_login(None, usuario)
    registrar_en_bitacora(request, "LOGIN", usuario, entidad_id=usuario.id)

    return Response({"token": token.key, "usuario": UsuarioSerializer(usuario).data})


@api_view(["POST"])
def logout(request):
    registrar_en_bitacora(request, "LOGOUT", request.user, entidad_id=request.user.id)
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def usuario_actual(request):
    return Response(UsuarioSerializer(request.user).data)


# Administración de usuarios

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
