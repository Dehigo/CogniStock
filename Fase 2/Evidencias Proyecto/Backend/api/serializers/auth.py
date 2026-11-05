from rest_framework import serializers

from api.models import Usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=150)  # email completo o solo el usuario (lo que va antes de @)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source="rol.nombre", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol"]
