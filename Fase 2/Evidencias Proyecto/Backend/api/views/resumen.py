from django.db.models import F
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.models import AlertaStock, Cotizacion, Movimiento, Producto
from api.permissions import PuedeGestionarInventario


@api_view(["GET"])
@permission_classes([PuedeGestionarInventario])
def resumen(request):
    """Números para la pantalla de inicio del encargado: lo que necesita atención hoy."""
    hoy = timezone.localdate()
    movimientos_hoy = Movimiento.objects.filter(fecha__date=hoy)
    stock_bajo = Producto.objects.filter(activo=True, stock__cantidad__lt=F("stock_minimo")).order_by("stock__cantidad")

    return Response(
        {
            "stock_bajo": stock_bajo.count(),
            "alertas_activas": AlertaStock.objects.filter(estado="ACTIVA").count(),
            "cotizaciones_por_aprobar": Cotizacion.objects.filter(estado__codigo="REGISTRADA").count(),
            "cotizaciones_por_recibir": Cotizacion.objects.filter(estado__codigo="APROBADA").count(),
            "entradas_hoy": movimientos_hoy.filter(tipo="ENTRADA").count(),
            "salidas_hoy": movimientos_hoy.filter(tipo="SALIDA").count(),
            "productos_criticos": [
                {"codigo": p.codigo, "nombre": p.nombre, "stock": p.stock.cantidad, "minimo": p.stock_minimo}
                for p in stock_bajo.select_related("stock")[:5]
            ],
        }
    )
