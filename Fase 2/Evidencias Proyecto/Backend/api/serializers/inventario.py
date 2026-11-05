import re

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.models import CategoriaProducto, Producto, Proveedor

# Códigos que se imprimen o escanean: solo letras, números, punto, guion y guion bajo (sin espacios).
CODIGO_PERMITIDO = re.compile(r"[A-Za-z0-9._-]*")


def codigo_valido(codigo):
    if not CODIGO_PERMITIDO.fullmatch(codigo):
        raise serializers.ValidationError("Usa solo letras, números, punto, guion o guion bajo, sin espacios.")
    return codigo


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProducto
        fields = ["id", "nombre", "descripcion", "activo"]
        extra_kwargs = {
            "nombre": {
                "validators": [
                    UniqueValidator(CategoriaProducto.objects.all(), "Ya existe una categoría con este nombre."),
                ],
            },
        }


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True, default=None)
    stock_actual = serializers.IntegerField(source="stock.cantidad", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "codigo",
            "codigo_qr",
            "nombre",
            "descripcion",
            "categoria",
            "categoria_nombre",
            "unidad_medida",
            "precio_referencia",
            "stock_minimo",
            "stock_actual",
            "activo",
            "creado_en",
        ]
        extra_kwargs = {
            "codigo": {
                "validators": [UniqueValidator(Producto.objects.all(), "Ya existe un producto con este código.")],
            },
            "codigo_qr": {
                "validators": [
                    UniqueValidator(Producto.objects.all(), "Ya existe un producto con este código de barras."),
                ],
            },
            "descripcion": {"max_length": 1000},
            "precio_referencia": {"min_value": 0},
            "stock_minimo": {"min_value": 0},
        }

    def validate_codigo(self, codigo):
        return codigo_valido(codigo)

    def validate_codigo_qr(self, codigo_qr):
        return codigo_valido(codigo_qr)

    def validate_categoria(self, categoria):
        # Una categoría inactiva no se asigna, pero el producto puede conservar la que ya tenía.
        actual = self.instance.categoria if self.instance else None
        if categoria and not categoria.activo and categoria != actual:
            raise serializers.ValidationError("La categoría está inactiva.")
        return categoria


class ProductoQrSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True, default=None)
    stock_actual = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "id",
            "codigo",
            "codigo_qr",
            "nombre",
            "descripcion",
            "categoria",
            "categoria_nombre",
            "unidad_medida",
            "stock_minimo",
            "stock_actual",
            "activo",
        ]

    def get_stock_actual(self, obj):
        stock = getattr(obj, "stock", None)
        if stock is None:
            return 0
        return stock.cantidad


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ["id", "nombre", "rut", "email", "telefono", "activo"]

    def validate_rut(self, rut):
        """Acepta 76.123.456-7, 76123456-7 o 761234567 y lo guarda como 76123456-7."""
        if not rut:
            return rut
        limpio = rut.upper().replace(".", "").replace("-", "")
        if not re.fullmatch(r"[0-9]{7,8}[0-9K]", limpio):
            raise serializers.ValidationError("El RUT no tiene un formato válido (ej.: 76.123.456-7).")
        cuerpo, dv = limpio[:-1], limpio[-1]
        # Dígito verificador (módulo 11).
        suma = sum(int(digito) * factor for digito, factor in zip(reversed(cuerpo), [2, 3, 4, 5, 6, 7] * 2))
        if dv != "0K987654321"[suma % 11]:
            raise serializers.ValidationError("El dígito verificador del RUT no es correcto.")

        rut = f"{cuerpo}-{dv}"
        repetidos = Proveedor.objects.filter(rut=rut)
        if self.instance:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError("Ya existe un proveedor con este RUT.")
        return rut

    def validate_telefono(self, telefono):
        if telefono and not re.fullmatch(r"\+?[0-9]{8,15}", telefono.replace(" ", "")):
            raise serializers.ValidationError("El teléfono debe tener entre 8 y 15 dígitos (ej.: +56 9 1234 5678).")
        return telefono
