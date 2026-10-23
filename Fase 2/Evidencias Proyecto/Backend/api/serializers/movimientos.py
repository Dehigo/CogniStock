from rest_framework import serializers

from api.models import Movimiento


class MovimientoSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source="producto.codigo", read_only=True)
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    referencia = serializers.SerializerMethodField()

    class Meta:
        model = Movimiento
        fields = [
            "id",
            "fecha",
            "tipo",
            "producto",
            "producto_codigo",
            "producto_nombre",
            "cantidad",
            "usuario_nombre",
            "referencia",
            "observaciones",
        ]

    def get_referencia(self, movimiento):
        if movimiento.entrada_id:
            return f"Entrada #{movimiento.entrada_id} · cotización {movimiento.entrada.cotizacion.numero}"
        return f"Salida #{movimiento.salida_id}"
