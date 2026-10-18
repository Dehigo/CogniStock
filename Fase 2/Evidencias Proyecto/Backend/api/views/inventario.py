from django.db import transaction
from django.db.models import F, Q
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.bitacora import registrar_en_bitacora
from api.models import (
    AlertaStock,
    CategoriaProducto,
    DetalleSalida,
    EscaneoQR,
    Movimiento,
    Producto,
    Proveedor,
    Salida,
    Stock,
)
from api.permissions import PuedeGestionarInventario
from api.serializers import CategoriaSerializer, ProductoQrSerializer, ProductoSerializer, ProveedorSerializer


def _registrar_alerta_stock(producto, stock_actual):
    if stock_actual > 0 and stock_actual >= producto.stock_minimo:
        return

    tipo = AlertaStock.Tipo.SIN_STOCK if stock_actual <= 0 else AlertaStock.Tipo.STOCK_BAJO
    alerta = AlertaStock.objects.filter(producto=producto, tipo=tipo, estado=AlertaStock.Estado.ACTIVA).first()
    if alerta is not None:
        alerta.cantidad_al_generar = stock_actual
        alerta.save(update_fields=["cantidad_al_generar"])
        return alerta

    return AlertaStock.objects.create(
        producto=producto,
        tipo=tipo,
        cantidad_al_generar=stock_actual,
        estado=AlertaStock.Estado.ACTIVA,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, PuedeGestionarInventario])
def producto_por_qr(request):
    codigo_qr = (request.query_params.get("codigo_qr") or "").strip()
    if not codigo_qr:
        return Response({"detail": "Se requiere el código QR.", "resultado": "QR_INVALIDO"}, status=status.HTTP_400_BAD_REQUEST)

    producto = Producto.objects.select_related("categoria", "stock").filter(codigo_qr=codigo_qr).first()
    if producto is None:
        return Response({"detail": "Código QR no reconocido.", "resultado": "QR_INVALIDO"}, status=status.HTTP_404_NOT_FOUND)

    if not producto.activo:
        return Response({"detail": "El producto está inactivo.", "resultado": "QR_INVALIDO"}, status=status.HTTP_409_CONFLICT)

    stock = getattr(producto, "stock", None)
    if stock is None:
        stock = Stock.objects.get_or_create(producto=producto, defaults={"cantidad": 0})[0]

    serializer = ProductoQrSerializer(producto)
    data = serializer.data
    data["stock_actual"] = stock.cantidad
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, PuedeGestionarInventario])
def registrar_salida(request):
    codigo_qr = (request.data.get("codigo_qr") or "").strip()
    observaciones = (request.data.get("observaciones") or "").strip()
    cantidad_raw = request.data.get("cantidad")

    if not codigo_qr:
        return Response({"detail": "Se requiere el código QR.", "resultado": "QR_INVALIDO"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cantidad = int(cantidad_raw)
    except (TypeError, ValueError):
        return Response({"detail": "La cantidad debe ser un entero mayor que 0.", "resultado": "QR_INVALIDO"}, status=status.HTTP_400_BAD_REQUEST)

    if cantidad <= 0:
        return Response({"detail": "La cantidad debe ser mayor que 0.", "resultado": "QR_INVALIDO"}, status=status.HTTP_400_BAD_REQUEST)

    producto = Producto.objects.select_related("categoria", "stock").filter(codigo_qr=codigo_qr).first()
    if producto is None:
        EscaneoQR.objects.create(
            codigo_leido=codigo_qr,
            producto=None,
            usuario=request.user,
            resultado=EscaneoQR.Resultado.QR_INVALIDO,
        )
        registrar_en_bitacora(
            request,
            "SALIDA_QR_INVALIDO",
            request.user,
            "productos",
            detalle={"codigo_qr": codigo_qr, "cantidad": cantidad},
        )
        return Response({"detail": "Código QR no reconocido.", "resultado": "QR_INVALIDO"}, status=status.HTTP_404_NOT_FOUND)

    if not producto.activo:
        EscaneoQR.objects.create(
            codigo_leido=codigo_qr,
            producto=producto,
            usuario=request.user,
            resultado=EscaneoQR.Resultado.QR_INVALIDO,
        )
        registrar_en_bitacora(
            request,
            "SALIDA_PRODUCTO_INACTIVO",
            request.user,
            "productos",
            entidad_id=producto.id,
            detalle={"codigo_qr": codigo_qr, "cantidad": cantidad},
        )
        return Response({"detail": "El producto está inactivo.", "resultado": "QR_INVALIDO"}, status=status.HTTP_409_CONFLICT)

    with transaction.atomic():
        stock, _ = Stock.objects.select_for_update().get_or_create(producto=producto, defaults={"cantidad": 0})
        if stock.cantidad < cantidad:
            EscaneoQR.objects.create(
                codigo_leido=codigo_qr,
                producto=producto,
                usuario=request.user,
                resultado=EscaneoQR.Resultado.SIN_STOCK,
            )
            registrar_en_bitacora(
                request,
                "SALIDA_STOCK_INSUFICIENTE",
                request.user,
                "productos",
                entidad_id=producto.id,
                detalle={"codigo_qr": codigo_qr, "cantidad": cantidad, "stock_actual": stock.cantidad},
            )
            return Response(
                {
                    "detail": "Stock insuficiente para la cantidad solicitada.",
                    "resultado": "SIN_STOCK",
                    "stock_actual": stock.cantidad,
                    "cantidad_solicitada": cantidad,
                },
                status=status.HTTP_409_CONFLICT,
            )

        salida = Salida.objects.create(usuario=request.user, observaciones=observaciones)
        DetalleSalida.objects.create(
            salida=salida,
            producto=producto,
            cantidad=cantidad,
            codigo_qr=codigo_qr,
        )
        stock.cantidad -= cantidad
        stock.save(update_fields=["cantidad", "actualizado_en"])
        Movimiento.objects.create(
            producto=producto,
            usuario=request.user,
            tipo=Movimiento.Tipo.SALIDA,
            cantidad=cantidad,
            salida=salida,
            observaciones=observaciones,
        )
        EscaneoQR.objects.create(
            codigo_leido=codigo_qr,
            producto=producto,
            usuario=request.user,
            resultado=EscaneoQR.Resultado.OK,
            salida=salida,
        )
        _registrar_alerta_stock(producto, stock.cantidad)
        registrar_en_bitacora(
            request,
            "SALIDA_REGISTRADA",
            request.user,
            "salidas",
            entidad_id=salida.id,
            detalle={
                "codigo_qr": codigo_qr,
                "cantidad": cantidad,
                "stock_restante": stock.cantidad,
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
                    "stock_actual": stock.cantidad,
                },
                "cantidad": cantidad,
                "stock_restante": stock.cantidad,
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
