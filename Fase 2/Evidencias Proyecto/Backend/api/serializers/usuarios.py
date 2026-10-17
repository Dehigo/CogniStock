from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from api.models import Rol, Usuario


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["id", "nombre", "descripcion"]


class UsuarioAdminSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=150)
    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all())
    rol_nombre = serializers.CharField(source="rol.nombre", read_only=True)
    activo = serializers.BooleanField(source="is_active", required=False)
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    creado_en = serializers.DateTimeField(source="date_joined", read_only=True)
    ultimo_acceso = serializers.DateTimeField(source="last_login", read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "nombre",
            "email",
            "rol",
            "rol_nombre",
            "activo",
            "password",
            "creado_en",
            "ultimo_acceso",
        ]

    def validate_email(self, email):
        existentes = Usuario.objects.filter(email__iexact=email)
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return email

    def validate(self, attrs):
        password = attrs.get("password")

        if self.instance is None and not password:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})

        if password:
            datos = {campo: valor for campo, valor in attrs.items() if campo != "password"}
            usuario = self.instance or Usuario(**datos)
            try:
                validate_password(password, usuario)
            except DjangoValidationError as error:
                raise serializers.ValidationError({"password": list(error.messages)})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        return Usuario.objects.create_user(email, password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
