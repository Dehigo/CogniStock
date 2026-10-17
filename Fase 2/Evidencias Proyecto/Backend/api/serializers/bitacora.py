from rest_framework import serializers

from api.models import BitacoraAuditoria


class BitacoraSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True, default=None)

    class Meta:
        model = BitacoraAuditoria
        fields = ["id", "fecha", "usuario_nombre", "accion", "entidad", "entidad_id", "detalle", "ip"]
