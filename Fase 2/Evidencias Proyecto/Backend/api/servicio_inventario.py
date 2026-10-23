"""Servicio central de inventario: el único lugar donde cambia el stock (RB-001..004, RB-P03).

Cada operación bloquea la fila de stock, genera su movimiento y deja todo en una sola transacción.
"""

from django.db import transaction
from django.db.models import Sum

from api.models import (
    AlertaStock,
    Cotizacion,
    DetalleEntrada,
    DetalleSalida,
    Entrada,
    EscaneoQR,
    EstadoCotizacion,
    HistorialEstadoCotizacion,
    Movimiento,
    Producto,
    Salida,
    Stock,
)

# Propuesta D-11: RECIBIDA no se elige a mano, la asigna registrar_entrada al completar la cotización.
TRANSICIONES_COTIZACION = {
    "REGISTRADA": {"APROBADA", "ANULADA"},
    "APROBADA": {"ANULADA", "RECIBIDA"},
}


class OperacionRechazada(Exception):
    def __init__(self, resultado, mensaje, producto=None, **datos):
        super().__init__(mensaje)
        self.resultado = resultado
        self.mensaje = mensaje
        self.producto = producto
        self.datos = datos


def buscar_producto_por_qr(codigo_qr):
    codigo_qr = str(codigo_qr or "").strip()
    if not codigo_qr:
        raise OperacionRechazada("QR_REQUERIDO", "Se requiere el código QR.")

    producto = Producto.objects.select_related("categoria", "stock").filter(codigo_qr=codigo_qr).first()
    if producto is None:
        raise OperacionRechazada("QR_INVALIDO", "Código QR no reconocido.")
    if not producto.activo:
        raise OperacionRechazada("PRODUCTO_INACTIVO", "El producto está inactivo.", producto)
    return producto


def _validar_cantidad(cantidad):
    if isinstance(cantidad, bool) or (isinstance(cantidad, float) and not cantidad.is_integer()):
        cantidad = None
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad <= 0:
        raise OperacionRechazada("CANTIDAD_INVALIDA", "La cantidad debe ser un entero mayor que 0.")
    return cantidad


def _actualizar_alerta_stock(producto, stock_actual):
    if stock_actual > 0 and stock_actual >= producto.stock_minimo:
        return

    tipo = AlertaStock.Tipo.SIN_STOCK if stock_actual <= 0 else AlertaStock.Tipo.STOCK_BAJO
    alerta = AlertaStock.objects.filter(producto=producto, tipo=tipo, estado=AlertaStock.Estado.ACTIVA).first()
    if alerta is not None:
        alerta.cantidad_al_generar = stock_actual
        alerta.save(update_fields=["cantidad_al_generar"])
        return

    AlertaStock.objects.create(producto=producto, tipo=tipo, cantidad_al_generar=stock_actual)


def registrar_salida(usuario, codigo_qr, cantidad, observaciones=""):
    """Descuenta stock de un producto identificado por QR (RF-08). Devuelve (salida, stock_restante)."""
    cantidad = _validar_cantidad(cantidad)
    observaciones = (observaciones or "").strip()

    try:
        producto = buscar_producto_por_qr(codigo_qr)
        with transaction.atomic():
            stock, _ = Stock.objects.select_for_update().get_or_create(producto=producto, defaults={"cantidad": 0})
            if stock.cantidad < cantidad:
                raise OperacionRechazada(
                    "SIN_STOCK",
                    "Stock insuficiente para la cantidad solicitada.",
                    producto,
                    stock_actual=stock.cantidad,
                    cantidad_solicitada=cantidad,
                )

            salida = Salida.objects.create(usuario=usuario, observaciones=observaciones)
            DetalleSalida.objects.create(salida=salida, producto=producto, cantidad=cantidad, codigo_qr=producto.codigo_qr)
            stock.cantidad -= cantidad
            stock.save(update_fields=["cantidad", "actualizado_en"])
            Movimiento.objects.create(
                producto=producto,
                usuario=usuario,
                tipo=Movimiento.Tipo.SALIDA,
                cantidad=cantidad,
                salida=salida,
                observaciones=observaciones,
            )
            EscaneoQR.objects.create(
                codigo_leido=producto.codigo_qr,
                producto=producto,
                usuario=usuario,
                resultado=EscaneoQR.Resultado.OK,
                salida=salida,
            )
            _actualizar_alerta_stock(producto, stock.cantidad)
    except OperacionRechazada as rechazo:
        # El escaneo fallido queda registrado fuera de la transacción revertida.
        if rechazo.resultado != "QR_REQUERIDO":
            EscaneoQR.objects.create(
                codigo_leido=str(codigo_qr).strip(),
                producto=rechazo.producto,
                usuario=usuario,
                resultado=EscaneoQR.Resultado.SIN_STOCK if rechazo.resultado == "SIN_STOCK" else EscaneoQR.Resultado.QR_INVALIDO,
            )
        raise

    return salida, stock.cantidad


def obtener_estado_cotizacion(codigo):
    estado = EstadoCotizacion.objects.filter(codigo=codigo).first()
    if estado is None:
        raise OperacionRechazada(
            "CATALOGO_FALTANTE",
            f"No existe el estado {codigo}. Ejecuta: python manage.py cargar_catalogos",
        )
    return estado


def cambiar_estado_cotizacion(cotizacion, codigo, usuario, motivo=""):
    anterior = cotizacion.estado
    if codigo not in TRANSICIONES_COTIZACION.get(anterior.codigo, set()):
        raise OperacionRechazada(
            "TRANSICION_INVALIDA", f"Una cotización {anterior.codigo} no puede pasar a {codigo}."
        )

    cotizacion.estado = obtener_estado_cotizacion(codigo)
    cotizacion.save(update_fields=["estado"])
    HistorialEstadoCotizacion.objects.create(
        cotizacion=cotizacion,
        estado_anterior=anterior,
        estado_nuevo=cotizacion.estado,
        usuario=usuario,
        motivo=(motivo or "").strip(),
    )


def cantidades_recibidas(cotizacion):
    filas = (
        DetalleEntrada.objects.filter(entrada__cotizacion=cotizacion)
        .values("producto")
        .annotate(total=Sum("cantidad"))
    )
    return {fila["producto"]: fila["total"] for fila in filas}


def registrar_entrada(usuario, cotizacion_id, detalles, observaciones=""):
    """Suma stock con lo recibido de una cotización válida (RF-06, RB-001, RB-002). Devuelve la entrada."""
    if not cotizacion_id:
        raise OperacionRechazada("COTIZACION_REQUERIDA", "Toda entrada debe estar asociada a una cotización.")
    if not detalles:
        raise OperacionRechazada("SIN_DETALLE", "La entrada debe incluir al menos un producto.")

    with transaction.atomic():
        # Bloquear la cotización evita que dos entradas simultáneas superen lo cotizado.
        cotizacion = (
            Cotizacion.objects.select_for_update().select_related("estado").filter(pk=cotizacion_id).first()
        )
        if cotizacion is None:
            raise OperacionRechazada("COTIZACION_INEXISTENTE", "La cotización no existe.")
        if not cotizacion.estado.permite_entrada:
            raise OperacionRechazada(
                "COTIZACION_NO_VALIDA",
                f"La cotización {cotizacion.numero} está {cotizacion.estado.codigo} y no permite entradas.",
            )

        cotizadas = dict(cotizacion.detalles.values_list("producto_id", "cantidad"))
        recibidas = cantidades_recibidas(cotizacion)
        cantidades = {}
        for detalle in detalles:
            producto_id = detalle.get("producto")
            producto_id = int(producto_id) if str(producto_id).isdigit() else None
            cantidad = _validar_cantidad(detalle.get("cantidad"))
            if producto_id in cantidades:
                raise OperacionRechazada("PRODUCTO_REPETIDO", "Un producto aparece dos veces en la entrada.")
            # Propuestas RB-P01 y RB-P02: solo productos cotizados y sin superar lo cotizado.
            if producto_id not in cotizadas:
                raise OperacionRechazada(
                    "PRODUCTO_NO_COTIZADO", "Uno de los productos no pertenece a la cotización."
                )
            pendiente = cotizadas[producto_id] - recibidas.get(producto_id, 0)
            if cantidad > pendiente:
                raise OperacionRechazada(
                    "EXCEDE_COTIZADO",
                    f"Se intenta ingresar {cantidad} y solo quedan {pendiente} por recibir de ese producto.",
                    producto_id=producto_id,
                    pendiente=pendiente,
                )
            cantidades[producto_id] = cantidad

        productos = Producto.objects.in_bulk(cantidades)
        inactivo = next((p for p in productos.values() if not p.activo), None)
        if inactivo is not None:
            raise OperacionRechazada("PRODUCTO_INACTIVO", f"El producto {inactivo.nombre} está inactivo.", inactivo)

        observaciones = (observaciones or "").strip()
        entrada = Entrada.objects.create(cotizacion=cotizacion, usuario=usuario, observaciones=observaciones)
        for producto_id in sorted(cantidades):
            producto, cantidad = productos[producto_id], cantidades[producto_id]
            DetalleEntrada.objects.create(entrada=entrada, producto=producto, cantidad=cantidad)
            stock, _ = Stock.objects.select_for_update().get_or_create(producto=producto, defaults={"cantidad": 0})
            stock.cantidad += cantidad
            stock.save(update_fields=["cantidad", "actualizado_en"])
            Movimiento.objects.create(
                producto=producto,
                usuario=usuario,
                tipo=Movimiento.Tipo.ENTRADA,
                cantidad=cantidad,
                entrada=entrada,
                observaciones=observaciones,
            )
            recibidas[producto_id] = recibidas.get(producto_id, 0) + cantidad

        if all(recibidas.get(producto_id, 0) >= cantidad for producto_id, cantidad in cotizadas.items()):
            cambiar_estado_cotizacion(cotizacion, "RECIBIDA", usuario, "Recepción completa.")

    return entrada
