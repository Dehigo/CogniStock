"""Servicio central de inventario: el ÚNICO lugar donde cambia el stock (RB-001 a RB-004, RB-P03).

Cada operación ocurre dentro de una transacción: o se guarda todo, o no se guarda nada.
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

# A qué estados puede pasar cada estado de cotización (propuesta D-11).
# RECIBIDA no se elige a mano: la pone registrar_entrada cuando llega todo.
TRANSICIONES = {
    "REGISTRADA": ["APROBADA", "ANULADA"],
    "APROBADA": ["ANULADA", "RECIBIDA"],
}


class Rechazo(Exception):
    """Una operación no permitida. Lleva un código, un mensaje y el estado HTTP para responder."""

    def __init__(self, codigo, mensaje, http=409, producto=None, **extra):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.http = http
        self.producto = producto
        self.extra = extra


def cantidad_valida(valor):
    # Acepta 3 o "3". Rechaza 0, negativos, decimales, texto y vacío.
    if not str(valor).isdecimal() or int(valor) == 0:
        raise Rechazo("CANTIDAD_INVALIDA", "La cantidad debe ser un entero mayor que 0.", 400)
    return int(valor)


def buscar_producto_por_qr(codigo_qr):
    codigo_qr = str(codigo_qr or "").strip()
    if not codigo_qr:
        raise Rechazo("QR_REQUERIDO", "Se requiere el código QR.", 400)

    producto = Producto.objects.select_related("categoria", "stock").filter(codigo_qr=codigo_qr).first()
    if producto is None:
        raise Rechazo("QR_INVALIDO", "Código QR no reconocido.", 404)
    if not producto.activo:
        raise Rechazo("PRODUCTO_INACTIVO", "El producto está inactivo.", producto=producto)
    return producto


def _revisar_alerta(producto, stock):
    if stock >= producto.stock_minimo and stock > 0:
        return
    tipo = AlertaStock.Tipo.SIN_STOCK if stock == 0 else AlertaStock.Tipo.STOCK_BAJO
    # Solo puede haber una alerta activa por producto y tipo: si ya existe, se actualiza.
    AlertaStock.objects.update_or_create(
        producto=producto, tipo=tipo, estado=AlertaStock.Estado.ACTIVA, defaults={"cantidad_al_generar": stock}
    )


def registrar_salida(usuario, codigo_qr, cantidad, observaciones=""):
    """Resta stock de un producto identificado por su QR (RF-08). Devuelve (salida, stock que queda)."""
    cantidad = cantidad_valida(cantidad)
    observaciones = (observaciones or "").strip()

    try:
        producto = buscar_producto_por_qr(codigo_qr)
        with transaction.atomic():
            # select_for_update bloquea la fila: dos salidas a la vez no pueden dejar stock negativo.
            stock = Stock.objects.select_for_update().get_or_create(producto=producto)[0]
            if stock.cantidad < cantidad:
                raise Rechazo(
                    "SIN_STOCK",
                    "Stock insuficiente para la cantidad solicitada.",
                    producto=producto,
                    stock_actual=stock.cantidad,
                    cantidad_solicitada=cantidad,
                )

            stock.cantidad -= cantidad
            stock.save()
            salida = Salida.objects.create(usuario=usuario, observaciones=observaciones)
            DetalleSalida.objects.create(salida=salida, producto=producto, cantidad=cantidad, codigo_qr=producto.codigo_qr)
            Movimiento.objects.create(
                producto=producto, usuario=usuario, tipo="SALIDA", cantidad=cantidad, salida=salida, observaciones=observaciones
            )
            EscaneoQR.objects.create(
                codigo_leido=producto.codigo_qr, producto=producto, usuario=usuario, resultado="OK", salida=salida
            )
            _revisar_alerta(producto, stock.cantidad)
    except Rechazo as rechazo:
        # Los escaneos fallidos también quedan registrados (menos cuando no se envió QR).
        if rechazo.codigo != "QR_REQUERIDO":
            EscaneoQR.objects.create(
                codigo_leido=str(codigo_qr).strip(),
                producto=rechazo.producto,
                usuario=usuario,
                resultado="SIN_STOCK" if rechazo.codigo == "SIN_STOCK" else "QR_INVALIDO",
            )
        raise

    return salida, stock.cantidad


def estado_cotizacion(codigo):
    estado = EstadoCotizacion.objects.filter(codigo=codigo).first()
    if estado is None:
        raise Rechazo("CATALOGO_FALTANTE", f"Falta el estado {codigo}. Ejecuta: python manage.py cargar_catalogos")
    return estado


def cambiar_estado_cotizacion(cotizacion, codigo, usuario, motivo=""):
    anterior = cotizacion.estado
    if codigo not in TRANSICIONES.get(anterior.codigo, []):
        raise Rechazo("TRANSICION_INVALIDA", f"Una cotización {anterior.codigo} no puede pasar a {codigo}.")

    cotizacion.estado = estado_cotizacion(codigo)
    cotizacion.save()
    HistorialEstadoCotizacion.objects.create(
        cotizacion=cotizacion,
        estado_anterior=anterior,
        estado_nuevo=cotizacion.estado,
        usuario=usuario,
        motivo=(motivo or "").strip(),
    )


def cantidades_recibidas(cotizacion):
    """Cuánto ha llegado de cada producto de la cotización: {producto_id: total}."""
    filas = DetalleEntrada.objects.filter(entrada__cotizacion=cotizacion).values("producto").annotate(total=Sum("cantidad"))
    return {fila["producto"]: fila["total"] for fila in filas}


def registrar_entrada(usuario, cotizacion_id, detalles, observaciones=""):
    """Suma stock con lo que llegó de una cotización aprobada (RF-06, RB-001, RB-002). Devuelve la entrada."""
    if not str(cotizacion_id).isdecimal():
        raise Rechazo("COTIZACION_REQUERIDA", "Toda entrada debe estar asociada a una cotización.", 400)
    if not isinstance(detalles, list) or not detalles or not all(isinstance(d, dict) for d in detalles):
        raise Rechazo("SIN_DETALLE", "La entrada debe incluir al menos un producto.", 400)

    with transaction.atomic():
        # Bloquear la cotización evita que dos entradas al mismo tiempo superen lo cotizado.
        cotizacion = Cotizacion.objects.select_for_update().select_related("estado").filter(pk=cotizacion_id).first()
        if cotizacion is None:
            raise Rechazo("COTIZACION_INEXISTENTE", "La cotización no existe.", 404)
        if not cotizacion.estado.permite_entrada:
            raise Rechazo(
                "COTIZACION_NO_VALIDA",
                f"La cotización {cotizacion.numero} está {cotizacion.estado.codigo} y no permite entradas.",
            )

        cotizado = dict(cotizacion.detalles.values_list("producto_id", "cantidad"))
        recibido = cantidades_recibidas(cotizacion)

        # 1) Revisar todo antes de guardar nada.
        llega = {}
        for detalle in detalles:
            producto_id = int(detalle["producto"]) if str(detalle.get("producto")).isdecimal() else None
            cantidad = cantidad_valida(detalle.get("cantidad"))
            if producto_id in llega:
                raise Rechazo("PRODUCTO_REPETIDO", "Un producto aparece dos veces en la entrada.", 400)
            if producto_id not in cotizado:  # RB-P01
                raise Rechazo("PRODUCTO_NO_COTIZADO", "Uno de los productos no pertenece a la cotización.")
            pendiente = cotizado[producto_id] - recibido.get(producto_id, 0)
            if cantidad > pendiente:  # RB-P02
                raise Rechazo(
                    "EXCEDE_COTIZADO",
                    f"Se intenta ingresar {cantidad} y solo quedan {pendiente} por recibir de ese producto.",
                    producto_id=producto_id,
                    pendiente=pendiente,
                )
            llega[producto_id] = cantidad

        productos = Producto.objects.in_bulk(llega)
        for producto in productos.values():
            if not producto.activo:
                raise Rechazo("PRODUCTO_INACTIVO", f"El producto {producto.nombre} está inactivo.", producto=producto)

        # 2) Guardar: entrada, y por cada producto su detalle, stock y movimiento.
        observaciones = (observaciones or "").strip()
        entrada = Entrada.objects.create(cotizacion=cotizacion, usuario=usuario, observaciones=observaciones)
        for producto_id, cantidad in sorted(llega.items()):  # en orden, para bloquear siempre igual
            producto = productos[producto_id]
            stock = Stock.objects.select_for_update().get_or_create(producto=producto)[0]
            stock.cantidad += cantidad
            stock.save()
            DetalleEntrada.objects.create(entrada=entrada, producto=producto, cantidad=cantidad)
            Movimiento.objects.create(
                producto=producto, usuario=usuario, tipo="ENTRADA", cantidad=cantidad, entrada=entrada, observaciones=observaciones
            )
            recibido[producto_id] = recibido.get(producto_id, 0) + cantidad

        # 3) Si ya llegó todo lo cotizado, la cotización pasa sola a RECIBIDA.
        if all(recibido.get(producto_id, 0) >= cantidad for producto_id, cantidad in cotizado.items()):
            cambiar_estado_cotizacion(cotizacion, "RECIBIDA", usuario, "Recepción completa.")

    return entrada
