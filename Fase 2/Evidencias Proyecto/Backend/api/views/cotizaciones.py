from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import servicio_inventario
from api.bitacora import registrar_en_bitacora
from api.models import Cotizacion, Entrada, EstadoCotizacion, Moneda
from api.permissions import PuedeGestionarInventario
from api.serializers import (
    CotizacionSerializer,
    EntradaSerializer,
    EstadoCotizacionSerializer,
    MonedaSerializer,
    NuevaEntradaSerializer,
)
from api.views.inventario import respuesta_rechazo

LIMITE_ENTRADAS = 200


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
        cotizaciones = (
            Cotizacion.objects.select_related("proveedor", "moneda", "estado", "creado_por")
            .prefetch_related("detalles__producto")
            .order_by("-fecha", "-id")
        )
        parametros = self.request.query_params

        buscar = parametros.get("buscar", "").strip()
        if buscar:
            cotizaciones = cotizaciones.filter(Q(numero__icontains=buscar) | Q(proveedor__nombre__icontains=buscar))

        estado = parametros.get("estado")
        if estado:
            cotizaciones = cotizaciones.filter(estado__codigo=estado)

        proveedor = parametros.get("proveedor")
        if proveedor and proveedor.isdigit():
            cotizaciones = cotizaciones.filter(proveedor_id=proveedor)

        if parametros.get("permite_entrada") == "true":
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
        codigo = (request.data.get("estado") or "").strip().upper()
        if codigo == "RECIBIDA":
            return Response(
                {"detail": "Una cotización queda RECIBIDA sola al registrar todas sus entradas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            cotizacion = Cotizacion.objects.select_for_update().select_related("estado").get(pk=self.get_object().pk)
            try:
                servicio_inventario.cambiar_estado_cotizacion(
                    cotizacion, codigo, request.user, request.data.get("motivo")
                )
            except servicio_inventario.OperacionRechazada as rechazo:
                return respuesta_rechazo(rechazo)

        registrar_en_bitacora(
            request,
            f"COTIZACION_{codigo}",
            request.user,
            "cotizaciones",
            cotizacion.id,
            {"motivo": request.data.get("motivo")},
        )
        return Response(self.get_serializer(self.get_queryset().get(pk=cotizacion.pk)).data)


class EntradaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = EntradaSerializer
    permission_classes = [PuedeGestionarInventario]

    def get_queryset(self):
        entradas = (
            Entrada.objects.select_related("cotizacion__proveedor", "usuario")
            .prefetch_related("detalles__producto")
            .order_by("-fecha")
        )
        cotizacion = self.request.query_params.get("cotizacion")
        if cotizacion and cotizacion.isdigit():
            entradas = entradas.filter(cotizacion_id=cotizacion)
        return entradas

    def list(self, request, *args, **kwargs):
        entradas = self.get_queryset()[:LIMITE_ENTRADAS]
        return Response(self.get_serializer(entradas, many=True).data)

    def create(self, request, *args, **kwargs):
        datos = NuevaEntradaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        datos = datos.validated_data

        try:
            entrada = servicio_inventario.registrar_entrada(
                request.user, datos.get("cotizacion"), datos["detalles"], datos["observaciones"]
            )
        except servicio_inventario.OperacionRechazada as rechazo:
            registrar_en_bitacora(
                request,
                f"ENTRADA_RECHAZADA_{rechazo.resultado}",
                request.user,
                "entradas",
                detalle={"cotizacion": datos.get("cotizacion"), "detalles": datos["detalles"], **rechazo.datos},
            )
            return respuesta_rechazo(rechazo)

        registrar_en_bitacora(
            request,
            "ENTRADA_REGISTRADA",
            request.user,
            "entradas",
            entrada.id,
            {"cotizacion": entrada.cotizacion_id, "detalles": datos["detalles"]},
        )
        entrada = self.get_queryset().get(pk=entrada.pk)
        return Response(self.get_serializer(entrada).data, status=status.HTTP_201_CREATED)
