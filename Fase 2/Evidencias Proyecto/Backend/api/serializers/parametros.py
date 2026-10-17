from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.models import ParametroSistema


class ParametroSerializer(serializers.ModelSerializer):
    actualizado_por_nombre = serializers.CharField(source="actualizado_por.nombre", read_only=True, default=None)

    class Meta:
        model = ParametroSistema
        fields = ["id", "clave", "valor", "descripcion", "actualizado_por_nombre", "actualizado_en"]
        extra_kwargs = {
            "clave": {
                "validators": [
                    UniqueValidator(ParametroSistema.objects.all(), "Ya existe un parámetro con esta clave."),
                ],
            },
        }
