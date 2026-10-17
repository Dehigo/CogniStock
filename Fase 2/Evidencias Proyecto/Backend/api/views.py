from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from api.models import BitacoraAuditoria
from api.serializers import LoginSerializer, UsuarioSerializer


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


def registrar_en_bitacora(request, accion, usuario=None, detalle=None):
    BitacoraAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad="usuarios",
        entidad_id=usuario.id if usuario else None,
        detalle=detalle,
        ip=request.META.get("REMOTE_ADDR"),
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


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
    registrar_en_bitacora(request, "LOGIN", usuario)

    return Response({"token": token.key, "usuario": UsuarioSerializer(usuario).data})


@api_view(["POST"])
def logout(request):
    registrar_en_bitacora(request, "LOGOUT", request.user)
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def usuario_actual(request):
    return Response(UsuarioSerializer(request.user).data)
