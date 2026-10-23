from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api import servicio_inventario
from api.models import (
    Cotizacion,
    DetalleCotizacion,
    DetalleEntrada,
    Entrada,
    EstadoCotizacion,
    HistorialEstadoCotizacion,
    Moneda,
)


class MonedaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moneda
        fields = ["id", "codigo", "nombre", "simbolo"]


class EstadoCotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoCotizacion
        fields = ["id", "codigo", "descripcion", "permite_entrada"]


class DetalleCotizacionSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source="producto.codigo", read_only=True)
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = DetalleCotizacion
        fields = ["id", "producto", "producto_codigo", "producto_nombre", "cantidad", "precio_unitario"]
        extra_kwargs = {"cantidad": {"min_value": 1}, "precio_unitario": {"min_value": 0}}


class CotizacionSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)
    moneda_codigo = serializers.CharField(source="moneda.codigo", read_only=True)
    estado = serializers.CharField(source="estado.codigo", read_only=True)
    permite_entrada = serializers.BooleanField(source="estado.permite_entrada", read_only=True)
    creado_por_nombre = serializers.CharField(source="creado_por.nombre", read_only=True)
    detalles = DetalleCotizacionSerializer(many=True)

    class Meta:
        model = Cotizacion
        fields = [
            "id",
            "numero",
            "proveedor",
            "proveedor_nombre",
            "moneda",
            "moneda_codigo",
            "estado",
            "permite_entrada",
            "fecha",
            "observaciones",
            "detalles",
            "creado_por_nombre",
            "creado_en",
        ]
        extra_kwargs = {
            "numero": {
                "validators": [UniqueValidator(Cotizacion.objects.all(), "Ya existe una cotización con este número.")],
            },
        }

    def validate_proveedor(self, proveedor):
        if not proveedor.activo:
            raise serializers.ValidationError("El proveedor está inactivo.")
        return proveedor

    def validate_detalles(self, detalles):
        if not detalles:
            raise serializers.ValidationError("La cotización debe incluir al menos un producto.")
        productos = [detalle["producto"] for detalle in detalles]
        if len(productos) != len(set(productos)):
            raise serializers.ValidationError("Un producto aparece dos veces en la cotización.")
        inactivo = next((producto for producto in productos if not producto.activo), None)
        if inactivo is not None:
            raise serializers.ValidationError(f"El producto {inactivo.nombre} está inactivo.")
        return detalles

    def validate(self, datos):
        if self.instance is not None and self.instance.estado.codigo != "REGISTRADA":
            raise serializers.ValidationError("Solo se puede editar una cotización REGISTRADA.")
        return datos

    @transaction.atomic
    def create(self, datos):
        detalles = datos.pop("detalles")
        usuario = self.context["request"].user
        try:
            estado = servicio_inventario.obtener_estado_cotizacion("REGISTRADA")
        except servicio_inventario.OperacionRechazada as rechazo:
            raise serializers.ValidationError(rechazo.mensaje)

        cotizacion = Cotizacion.objects.create(**datos, estado=estado, creado_por=usuario)
        DetalleCotizacion.objects.bulk_create(DetalleCotizacion(cotizacion=cotizacion, **d) for d in detalles)
        HistorialEstadoCotizacion.objects.create(cotizacion=cotizacion, estado_nuevo=estado, usuario=usuario)
        return cotizacion

    @transaction.atomic
    def update(self, cotizacion, datos):
        detalles = datos.pop("detalles", None)
        cotizacion = super().update(cotizacion, datos)
        if detalles is not None:
            cotizacion.detalles.all().delete()
            DetalleCotizacion.objects.bulk_create(DetalleCotizacion(cotizacion=cotizacion, **d) for d in detalles)
        return cotizacion

    def to_representation(self, cotizacion):
        datos = super().to_representation(cotizacion)
        recibidas = servicio_inventario.cantidades_recibidas(cotizacion)
        total = 0
        for detalle in datos["detalles"]:
            recibida = recibidas.get(detalle["producto"], 0)
            detalle["cantidad_recibida"] = recibida
            detalle["cantidad_pendiente"] = max(detalle["cantidad"] - recibida, 0)
            total += detalle["cantidad"] * float(detalle["precio_unitario"])
        datos["total"] = round(total, 2)
        return datos


class DetalleEntradaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = DetalleEntrada
        fields = ["producto", "producto_nombre", "cantidad"]


class EntradaSerializer(serializers.ModelSerializer):
    cotizacion_numero = serializers.CharField(source="cotizacion.numero", read_only=True)
    proveedor_nombre = serializers.CharField(source="cotizacion.proveedor.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    detalles = DetalleEntradaSerializer(many=True, read_only=True)

    class Meta:
        model = Entrada
        fields = [
            "id",
            "cotizacion",
            "cotizacion_numero",
            "proveedor_nombre",
            "usuario_nombre",
            "fecha",
            "observaciones",
            "detalles",
        ]


class NuevaEntradaSerializer(serializers.Serializer):
    """Solo revisa la forma de los datos; las reglas las aplica registrar_entrada."""

    cotizacion = serializers.IntegerField(required=False, allow_null=True)
    detalles = serializers.ListField(child=serializers.DictField(), allow_empty=True)
    observaciones = serializers.CharField(required=False, allow_blank=True, default="")
