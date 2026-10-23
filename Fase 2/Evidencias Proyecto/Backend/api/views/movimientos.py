from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.response import Response

from api.models import Movimiento
from api.permissions import PuedeGestionarInventario
from api.serializers import MovimientoSerializer

LIMITE_REGISTROS = 500


class MovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """Historial de entradas y salidas (RF-09). Solo lectura: los movimientos no se editan (RB-P04)."""

    serializer_class = MovimientoSerializer
    permission_classes = [PuedeGestionarInventario]

    def get_queryset(self):
        movimientos = Movimiento.objects.select_related("producto", "usuario", "entrada__cotizacion").order_by(
            "-fecha", "-id"
        )
        parametros = self.request.query_params

        buscar = parametros.get("buscar", "").strip()
        if buscar:
            movimientos = movimientos.filter(
                Q(producto__nombre__icontains=buscar) | Q(producto__codigo__icontains=buscar)
            )

        producto = parametros.get("producto")
        if producto and producto.isdigit():
            movimientos = movimientos.filter(producto_id=producto)

        tipo = parametros.get("tipo")
        if tipo in Movimiento.Tipo.values:
            movimientos = movimientos.filter(tipo=tipo)

        desde = parse_date(parametros.get("desde") or "")
        if desde:
            movimientos = movimientos.filter(fecha__date__gte=desde)

        hasta = parse_date(parametros.get("hasta") or "")
        if hasta:
            movimientos = movimientos.filter(fecha__date__lte=hasta)

        return movimientos

    def list(self, request, *args, **kwargs):
        movimientos = self.get_queryset()[:LIMITE_REGISTROS]
        return Response(self.get_serializer(movimientos, many=True).data)
