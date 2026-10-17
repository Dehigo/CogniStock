from django.db import transaction
from django.db.models import F, Q
from rest_framework import status, viewsets
from rest_framework.response import Response

from api.bitacora import registrar_en_bitacora
from api.models import CategoriaProducto, Producto, Proveedor, Stock
from api.permissions import PuedeGestionarInventario
from api.serializers import CategoriaSerializer, ProductoSerializer, ProveedorSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [PuedeGestionarInventario]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        categorias = CategoriaProducto.objects.order_by("nombre")

        activo = self.request.query_params.get("activo")
        if activo in ("true", "false"):
            categorias = categorias.filter(activo=activo == "true")

        return categorias

    def perform_create(self, serializer):
        categoria = serializer.save()
        registrar_en_bitacora(self.request, "CATEGORIA_CREADA", self.request.user, "categorias", categoria.id)

    def perform_update(self, serializer):
        categoria = serializer.save()
        registrar_en_bitacora(self.request, "CATEGORIA_EDITADA", self.request.user, "categorias", categoria.id)

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        categoria.activo = False
        categoria.save(update_fields=["activo"])
        registrar_en_bitacora(request, "CATEGORIA_DESACTIVADA", request.user, "categorias", categoria.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductoViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoSerializer
    permission_classes = [PuedeGestionarInventario]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        productos = Producto.objects.select_related("categoria", "stock").order_by("nombre")
        parametros = self.request.query_params

        buscar = parametros.get("buscar", "").strip()
        if buscar:
            productos = productos.filter(Q(nombre__icontains=buscar) | Q(codigo__icontains=buscar))

        categoria = parametros.get("categoria")
        if categoria and categoria.isdigit():
            productos = productos.filter(categoria_id=categoria)

        activo = parametros.get("activo")
        if activo in ("true", "false"):
            productos = productos.filter(activo=activo == "true")

        if parametros.get("stock_bajo") == "true":
            productos = productos.filter(stock__cantidad__lt=F("stock_minimo"))

        return productos

    @transaction.atomic
    def perform_create(self, serializer):
        producto = serializer.save()
        Stock.objects.create(producto=producto, cantidad=0)
        registrar_en_bitacora(self.request, "PRODUCTO_CREADO", self.request.user, "productos", producto.id)

    def perform_update(self, serializer):
        producto = serializer.save()
        registrar_en_bitacora(self.request, "PRODUCTO_EDITADO", self.request.user, "productos", producto.id)

    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        producto.activo = False
        producto.save(update_fields=["activo"])
        registrar_en_bitacora(request, "PRODUCTO_DESACTIVADO", request.user, "productos", producto.id)
        return Response(status=status.HTTP_204_NO_CONTENT)



class ProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = ProveedorSerializer
    permission_classes = [PuedeGestionarInventario]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        proveedores = Proveedor.objects.order_by("nombre")
        parametros = self.request.query_params

        buscar = parametros.get("buscar", "").strip()
        if buscar:
            proveedores = proveedores.filter(Q(nombre__icontains=buscar) | Q(rut__icontains=buscar))

        activo = parametros.get("activo")
        if activo in ("true", "false"):
            proveedores = proveedores.filter(activo=activo == "true")

        return proveedores

    def perform_create(self, serializer):
        proveedor = serializer.save()
        registrar_en_bitacora(self.request, "PROVEEDOR_CREADO", self.request.user, "proveedores", proveedor.id)

    def perform_update(self, serializer):
        proveedor = serializer.save()
        registrar_en_bitacora(self.request, "PROVEEDOR_EDITADO", self.request.user, "proveedores", proveedor.id)

    def destroy(self, request, *args, **kwargs):
        proveedor = self.get_object()
        proveedor.activo = False
        proveedor.save(update_fields=["activo"])
        registrar_en_bitacora(request, "PROVEEDOR_DESACTIVADO", request.user, "proveedores", proveedor.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
