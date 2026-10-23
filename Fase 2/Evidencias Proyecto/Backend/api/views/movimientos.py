from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import mixins, viewsets

from api.models import Movimiento
from api.permissions import PuedeGestionarInventario
from api.serializers import MovimientoSerializer


def _fecha(texto):
    """Convierte "2026-10-23" en fecha. Si no es una fecha válida, devuelve None y el filtro se ignora."""
    try:
        return parse_date(texto or "")
    except ValueError:
        return None


class MovimientoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Historial de las últimas 500 entradas y salidas (RF-09). Solo lectura: no se editan (RB-P04)."""

    serializer_class = MovimientoSerializer
    permission_classes = [PuedeGestionarInventario]

    def get_queryset(self):
        movimientos = Movimiento.objects.select_related("producto", "usuario", "entrada__cotizacion")
        movimientos = movimientos.order_by("-fecha", "-id")
        filtros = self.request.query_params

        if filtros.get("buscar"):
            texto = filtros["buscar"].strip()
            movimientos = movimientos.filter(Q(producto__nombre__icontains=texto) | Q(producto__codigo__icontains=texto))
        if filtros.get("producto", "").isdecimal():
            movimientos = movimientos.filter(producto_id=filtros["producto"])
        if filtros.get("tipo") in ("ENTRADA", "SALIDA"):
            movimientos = movimientos.filter(tipo=filtros["tipo"])
        desde, hasta = _fecha(filtros.get("desde")), _fecha(filtros.get("hasta"))
        if desde:
            movimientos = movimientos.filter(fecha__date__gte=desde)
        if hasta:
            movimientos = movimientos.filter(fecha__date__lte=hasta)
        return movimientos[:500]
