from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from api import agente
from api.bitacora import registrar_en_bitacora
from api.models import RecomendacionReposicion
from api.permissions import PuedeGestionarInventario

LARGO_MAXIMO_PREGUNTA = 500


class AgenteRateThrottle(UserRateThrottle):
    scope = "agente"


@api_view(["POST"])
@throttle_classes([AgenteRateThrottle])
def consultar_agente(request):
    pregunta = str(request.data.get("pregunta") or "").strip()
    if not pregunta:
        return Response({"detail": "Escribe una pregunta."}, status=status.HTTP_400_BAD_REQUEST)
    if len(pregunta) > LARGO_MAXIMO_PREGUNTA:
        return Response(
            {"detail": f"La pregunta no puede superar {LARGO_MAXIMO_PREGUNTA} caracteres."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        conversacion = agente.consultar(request.user, pregunta)
    except agente.AgenteNoDisponible as error:
        return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    herramientas = list(conversacion.ejecuciones_tool.values("tool", "permitido"))
    propuestas = list(
        conversacion.recomendaciones.values("id", "producto__nombre", "cantidad_sugerida", "justificacion")
    )
    return Response(
        {
            "id": conversacion.id,
            "pregunta": conversacion.pregunta,
            "respuesta": conversacion.respuesta,
            "herramientas": herramientas,
            "propuestas": propuestas,
        }
    )


class RecomendacionSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source="producto.codigo", read_only=True)
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    revisada_por_nombre = serializers.CharField(source="revisada_por.nombre", read_only=True, default=None)

    class Meta:
        model = RecomendacionReposicion
        fields = [
            "id",
            "producto",
            "producto_codigo",
            "producto_nombre",
            "cantidad_sugerida",
            "justificacion",
            "estado",
            "creada_en",
            "revisada_por_nombre",
            "revisada_en",
        ]


class RecomendacionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Propuestas del agente. Aceptar solo registra la decisión humana; no compra ni cambia stock."""

    serializer_class = RecomendacionSerializer
    permission_classes = [PuedeGestionarInventario]

    def get_queryset(self):
        recomendaciones = RecomendacionReposicion.objects.select_related("producto", "revisada_por").order_by(
            "-creada_en"
        )
        estado = self.request.query_params.get("estado")
        if estado in RecomendacionReposicion.Estado.values:
            recomendaciones = recomendaciones.filter(estado=estado)
        return recomendaciones[:200]

    @action(detail=True, methods=["post"])
    def revisar(self, request, pk=None):
        decision = str(request.data.get("estado") or "").upper()
        if decision not in ("ACEPTADA", "DESCARTADA"):
            return Response({"detail": "El estado debe ser ACEPTADA o DESCARTADA."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            recomendacion = RecomendacionReposicion.objects.select_for_update().filter(pk=pk).first()
            if recomendacion is None:
                return Response({"detail": "No existe la recomendación."}, status=status.HTTP_404_NOT_FOUND)
            if recomendacion.estado != RecomendacionReposicion.Estado.PROPUESTA:
                return Response({"detail": "La recomendación ya fue revisada."}, status=status.HTTP_409_CONFLICT)
            recomendacion.estado = decision
            recomendacion.revisada_por = request.user
            recomendacion.revisada_en = timezone.now()
            recomendacion.save(update_fields=["estado", "revisada_por", "revisada_en"])

        registrar_en_bitacora(request, f"RECOMENDACION_{decision}", request.user, "recomendaciones", recomendacion.id)
        return Response(self.get_serializer(recomendacion).data)
