from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import servicio_inventario
from api.bitacora import registrar_en_bitacora
from api.models import Cotizacion, Entrada, EstadoCotizacion, Moneda
from api.permissions import PuedeGestionarInventario
from api.serializers import CotizacionSerializer, EntradaSerializer, EstadoCotizacionSerializer, MonedaSerializer
from api.servicio_inventario import Rechazo
from api.views.inventario import respuesta_rechazo


class MonedaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Moneda.objects.order_by("codigo")
    serializer_class = MonedaSerializer


class EstadoCotizacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstadoCotizacion.objects.order_by("id")
    serializer_class = EstadoCotizacionSerializer


class CotizacionViewSet(viewsets.ModelViewSet):
    serializer_class = CotizacionSerializer
    permission_classes = [PuedeGestionarInventario]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        cotizaciones = Cotizacion.objects.select_related("proveedor", "moneda", "estado", "creado_por")
        cotizaciones = cotizaciones.prefetch_related("detalles__producto").order_by("-fecha", "-id")
        filtros = self.request.query_params

        if filtros.get("buscar"):
            texto = filtros["buscar"].strip()
            cotizaciones = cotizaciones.filter(Q(numero__icontains=texto) | Q(proveedor__nombre__icontains=texto))
        if filtros.get("estado"):
            cotizaciones = cotizaciones.filter(estado__codigo=filtros["estado"])
        if filtros.get("proveedor", "").isdecimal():
            cotizaciones = cotizaciones.filter(proveedor_id=filtros["proveedor"])
        if filtros.get("permite_entrada") == "true":
            cotizaciones = cotizaciones.filter(estado__permite_entrada=True)
        return cotizaciones

    def perform_create(self, serializer):
        cotizacion = serializer.save()
        registrar_en_bitacora(self.request, "COTIZACION_CREADA", self.request.user, "cotizaciones", cotizacion.id)

    def perform_update(self, serializer):
        cotizacion = serializer.save()
        registrar_en_bitacora(self.request, "COTIZACION_EDITADA", self.request.user, "cotizaciones", cotizacion.id)

    @action(detail=True, methods=["post"])
    def estado(self, request, pk=None):
        """Aprobar o anular. RECIBIDA no se elige a mano: llega sola al completar las entradas."""
        codigo = str(request.data.get("estado") or "").strip().upper()
        motivo = request.data.get("motivo")
        if codigo == "RECIBIDA":
            mensaje = "Una cotización queda RECIBIDA sola al registrar todas sus entradas."
            return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            cotizacion = Cotizacion.objects.select_for_update().get(pk=self.get_object().pk)
            try:
                servicio_inventario.cambiar_estado_cotizacion(cotizacion, codigo, request.user, motivo)
            except Rechazo as rechazo:
                return respuesta_rechazo(rechazo)

        registrar_en_bitacora(request, f"COTIZACION_{codigo}", request.user, "cotizaciones", cotizacion.id, {"motivo": motivo})
        return Response(self.get_serializer(self.get_queryset().get(pk=cotizacion.pk)).data)


class EntradaViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Listar las últimas 200 entradas y registrar nuevas. No se editan ni se borran: el stock ya cambió."""

    serializer_class = EntradaSerializer
    permission_classes = [PuedeGestionarInventario]

    def get_queryset(self):
        entradas = Entrada.objects.select_related("cotizacion__proveedor", "usuario")
        entradas = entradas.prefetch_related("detalles__producto").order_by("-fecha")
        cotizacion = self.request.query_params.get("cotizacion", "")
        if cotizacion.isdecimal():
            entradas = entradas.filter(cotizacion_id=cotizacion)
        return entradas[:200]

    def create(self, request):
        datos = request.data
        try:
            entrada = servicio_inventario.registrar_entrada(
                request.user, datos.get("cotizacion"), datos.get("detalles"), datos.get("observaciones")
            )
        except Rechazo as rechazo:
            detalle = {"cotizacion": datos.get("cotizacion"), "detalles": datos.get("detalles"), **rechazo.extra}
            registrar_en_bitacora(request, f"ENTRADA_RECHAZADA_{rechazo.codigo}", request.user, "entradas", None, detalle)
            return respuesta_rechazo(rechazo)

        detalle = {"cotizacion": entrada.cotizacion_id, "detalles": datos.get("detalles")}
        registrar_en_bitacora(request, "ENTRADA_REGISTRADA", request.user, "entradas", entrada.id, detalle)
        return Response(self.get_serializer(entrada).data, status=status.HTTP_201_CREATED)
