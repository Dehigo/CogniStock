from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from api import servicio_inventario
from api.models import (
    CategoriaProducto,
    Cotizacion,
    DetalleCotizacion,
    HistorialEstadoCotizacion,
    Moneda,
    Producto,
    Proveedor,
    Rol,
    Stock,
    Usuario,
)

# Usuarios de la demo. La contraseña es simple a propósito: solo para presentar, nunca en producción.
CLAVE = "password"
USUARIOS = [
    ("admin@cognistock.cl", "Admin", Rol.ADMINISTRADOR),
    ("encargado@cognistock.cl", "Encargado", Rol.ENCARGADO),
    ("vendedor@cognistock.cl", "Vendedor", Rol.OPERATIVO),
]

CATEGORIAS = ["Herramientas", "Fijaciones", "Pinturas", "Seguridad"]

PROVEEDORES = [
    ("Ferretería Sur Ltda.", "76123456-0", "ventas@ferreteriasur.cl"),
    ("Distribuidora Norte SpA", "77654321-7", "contacto@distnorte.cl"),
    ("Importadora Andes S.A.", "96512345-8", "pedidos@impandes.cl"),
]

# código, nombre, categoría, precio de referencia, stock mínimo
PRODUCTOS = [
    ("MAR-01", "Martillo carpintero 16 oz", "Herramientas", 8990, 5),
    ("DES-01", "Juego de destornilladores 6 piezas", "Herramientas", 12990, 4),
    ("TAL-01", "Taladro percutor 650 W", "Herramientas", 39990, 2),
    ("CLA-01", "Clavos 2 pulgadas caja 1 kg", "Fijaciones", 2490, 20),
    ("TOR-01", "Tornillos volcanita caja 100", "Fijaciones", 3290, 15),
    ("TAR-01", "Tarugos 8 mm bolsa 50", "Fijaciones", 1990, 10),
    ("PIN-01", "Pintura látex blanca 1 galón", "Pinturas", 14990, 6),
    ("BRO-01", "Brocha 2 pulgadas", "Pinturas", 1490, 10),
    ("GUA-01", "Guantes de cabritilla", "Seguridad", 2990, 8),
    ("LEN-01", "Lentes de seguridad", "Seguridad", 2490, 8),
]

# número, proveedor, {producto: cantidad cotizada}, {producto: cantidad que ya llegó}, aprobar
COTIZACIONES = [
    ("COT-2026-001", "Ferretería Sur Ltda.", {"MAR-01": 20, "DES-01": 10, "CLA-01": 100, "TOR-01": 60},
     {"MAR-01": 20, "DES-01": 10, "CLA-01": 100, "TOR-01": 60}, True),  # queda RECIBIDA
    ("COT-2026-002", "Distribuidora Norte SpA", {"PIN-01": 12, "BRO-01": 30, "GUA-01": 20},
     {"PIN-01": 6, "BRO-01": 30, "GUA-01": 10}, True),  # queda APROBADA con entrada parcial
    ("COT-2026-003", "Importadora Andes S.A.", {"TAL-01": 5, "TAR-01": 40, "LEN-01": 20},
     {}, False),  # queda REGISTRADA, para aprobar en vivo
]

# Salidas del vendedor. Los clavos quedan bajo el mínimo para que aparezca una alerta.
SALIDAS = [("MAR-01", 4), ("CLA-01", 85), ("TOR-01", 10), ("BRO-01", 5), ("GUA-01", 3)]


class Command(BaseCommand):
    help = "Carga datos de demostración. Con --reiniciar borra TODA la base antes de cargarlos."

    def add_arguments(self, parser):
        parser.add_argument("--reiniciar", action="store_true", help="Borra todos los datos de la base antes de cargar.")

    def handle(self, *args, **options):
        if options["reiniciar"]:
            call_command("flush", interactive=False, verbosity=0)
        call_command("cargar_catalogos", verbosity=0)

        if Producto.objects.filter(codigo="MAR-01").exists():
            self.stdout.write("Los datos de demostración ya estaban cargados. Usa --reiniciar para empezar de cero.")
            return

        with transaction.atomic():
            self.cargar()
        self.stdout.write(self.style.SUCCESS(f"Datos de demostración cargados. Contraseña de los 3 usuarios: {CLAVE}"))

    def cargar(self):
        usuarios = {}
        for email, nombre, rol in USUARIOS:
            usuarios[rol] = Usuario.objects.filter(email=email).first() or Usuario.objects.create_user(
                email, CLAVE, nombre=nombre, rol=Rol.objects.get(nombre=rol)
            )
        encargado, vendedor = usuarios[Rol.ENCARGADO], usuarios[Rol.OPERATIVO]

        categorias = {nombre: CategoriaProducto.objects.get_or_create(nombre=nombre)[0] for nombre in CATEGORIAS}
        proveedores = {
            nombre: Proveedor.objects.create(nombre=nombre, rut=rut, email=email) for nombre, rut, email in PROVEEDORES
        }
        productos = {}
        for codigo, nombre, categoria, precio, minimo in PRODUCTOS:
            productos[codigo] = Producto.objects.create(
                codigo=codigo, codigo_qr=f"CS-{codigo}", nombre=nombre, categoria=categorias[categoria],
                precio_referencia=precio, stock_minimo=minimo,
            )
            Stock.objects.create(producto=productos[codigo], cantidad=0)

        # El stock se mueve con el servicio central, igual que desde la web: así quedan movimientos y alertas.
        registrada = servicio_inventario.estado_cotizacion("REGISTRADA")
        clp = Moneda.objects.get(codigo="CLP")
        for numero, proveedor, cotizado, llegado, aprobar in COTIZACIONES:
            cotizacion = Cotizacion.objects.create(
                numero=numero, proveedor=proveedores[proveedor], moneda=clp, estado=registrada, creado_por=encargado
            )
            for codigo, cantidad in cotizado.items():
                producto = productos[codigo]
                DetalleCotizacion.objects.create(
                    cotizacion=cotizacion, producto=producto, cantidad=cantidad, precio_unitario=producto.precio_referencia * 9 // 10
                )
            HistorialEstadoCotizacion.objects.create(cotizacion=cotizacion, estado_nuevo=registrada, usuario=encargado)
            if aprobar:
                servicio_inventario.cambiar_estado_cotizacion(cotizacion, "APROBADA", encargado)
            if llegado:
                detalles = [{"producto": productos[codigo].id, "cantidad": cantidad} for codigo, cantidad in llegado.items()]
                servicio_inventario.registrar_entrada(encargado, cotizacion.id, detalles, "Carga de demostración")

        for codigo, cantidad in SALIDAS:
            servicio_inventario.registrar_salida(vendedor, f"CS-{codigo}", cantidad, "Venta de mostrador")
