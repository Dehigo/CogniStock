from django.db import transaction
from django.db.models import F, Q
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import servicio_inventario
from api.bitacora import registrar_en_bitacora
from api.models import CategoriaProducto, Producto, Proveedor, Stock
from api.permissions import PuedeGestionarInventario
from api.serializers import CategoriaSerializer, ProductoQrSerializer, ProductoSerializer, ProveedorSerializer

ESTADO_HTTP_RECHAZO = {
    "QR_REQUERIDO": status.HTTP_400_BAD_REQUEST,
    "CANTIDAD_INVALIDA": status.HTTP_400_BAD_REQUEST,
    "QR_INVALIDO": status.HTTP_404_NOT_FOUND,
    "PRODUCTO_INACTIVO": status.HTTP_409_CONFLICT,
    "SIN_STOCK": status.HTTP_409_CONFLICT,
    "COTIZACION_REQUERIDA": status.HTTP_400_BAD_REQUEST,
    "SIN_DETALLE": status.HTTP_400_BAD_REQUEST,
    "PRODUCTO_REPETIDO": status.HTTP_400_BAD_REQUEST,
    "COTIZACION_INEXISTENTE": status.HTTP_404_NOT_FOUND,
    "COTIZACION_NO_VALIDA": status.HTTP_409_CONFLICT,
    "PRODUCTO_NO_COTIZADO": status.HTTP_409_CONFLICT,
    "EXCEDE_COTIZADO": status.HTTP_409_CONFLICT,
    "TRANSICION_INVALIDA": status.HTTP_409_CONFLICT,
    "CATALOGO_FALTANTE": status.HTTP_409_CONFLICT,
}


def respuesta_rechazo(rechazo):
    return Response(
        {"detail": rechazo.mensaje, "resultado": rechazo.resultado, **rechazo.datos},
        status=ESTADO_HTTP_RECHAZO.get(rechazo.resultado, status.HTTP_400_BAD_REQUEST),
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, PuedeGestionarInventario])
def producto_por_qr(request):
    try:
        producto = servicio_inventario.buscar_producto_por_qr(request.query_params.get("codigo_qr"))
    except servicio_inventario.OperacionRechazada as rechazo:
        return respuesta_rechazo(rechazo)
    return Response(ProductoQrSerializer(producto).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, PuedeGestionarInventario])
def registrar_salida(request):
    codigo_qr = request.data.get("codigo_qr")
    cantidad = request.data.get("cantidad")
    try:
        salida, stock_restante = servicio_inventario.registrar_salida(
            request.user, codigo_qr, cantidad, request.data.get("observaciones")
        )
    except servicio_inventario.OperacionRechazada as rechazo:
        registrar_en_bitacora(
            request,
            f"SALIDA_RECHAZADA_{rechazo.resultado}",
            request.user,
            "salidas",
            entidad_id=rechazo.producto.id if rechazo.producto else None,
            detalle={"codigo_qr": codigo_qr, "cantidad": cantidad, **rechazo.datos},
        )
        return respuesta_rechazo(rechazo)

    detalle = salida.detalles.select_related("producto").get()
    producto = detalle.producto
    registrar_en_bitacora(
        request,
        "SALIDA_REGISTRADA",
        request.user,
        "salidas",
        entidad_id=salida.id,
        detalle={
            "codigo_qr": producto.codigo_qr,
            "cantidad": detalle.cantidad,
            "stock_restante": stock_restante,
            "producto_id": producto.id,
        },
    )
    return Response(
        {
            "detail": "Salida registrada correctamente.",
            "resultado": "OK",
            "salida_id": salida.id,
            "producto": {
                "id": producto.id,
                "codigo": producto.codigo,
                "codigo_qr": producto.codigo_qr,
                "nombre": producto.nombre,
                "stock_actual": stock_restante,
            },
            "cantidad": detalle.cantidad,
            "stock_restante": stock_restante,
        },
        status=status.HTTP_201_CREATED,
    )


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
