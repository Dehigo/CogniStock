from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.models import CategoriaProducto, Producto, Proveedor


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
            "precio_referencia": {"min_value": 0},
            "stock_minimo": {"min_value": 0},
        }


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
