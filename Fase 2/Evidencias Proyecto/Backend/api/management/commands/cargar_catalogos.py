from django.core.management.base import BaseCommand

from api.models import EstadoCotizacion, Moneda, Rol

# Mismos datos que los INSERT de 07_schema_postgresql.sql.
ROLES = [
    (Rol.ADMINISTRADOR, "Gestiona usuarios, roles, parámetros y supervisa operaciones."),
    (Rol.ENCARGADO, "Registra cotizaciones y entradas, consulta stock y gestiona salidas."),
    ("Usuario operativo", "Consulta productos y ejecuta salidas mediante QR según permisos."),
]

ESTADOS_COTIZACION = [
    ("REGISTRADA", "Cotización ingresada, pendiente de aprobación.", False),
    ("APROBADA", "Cotización aprobada, ya se pueden registrar entradas.", True),
    ("RECIBIDA", "Los productos cotizados ya ingresaron al inventario.", False),
    ("ANULADA", "Cotización sin efecto.", False),
]

MONEDAS = [
    ("CLP", "Peso chileno", "$"),
    ("USD", "Dólar estadounidense", "US$"),
    ("EUR", "Euro", "€"),
]


class Command(BaseCommand):
    help = "Carga los catálogos base (roles, estados de cotización y monedas). Se puede ejecutar varias veces."

    def handle(self, *args, **options):
        for nombre, descripcion in ROLES:
            Rol.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})
        for codigo, descripcion, permite_entrada in ESTADOS_COTIZACION:
            EstadoCotizacion.objects.get_or_create(
                codigo=codigo, defaults={"descripcion": descripcion, "permite_entrada": permite_entrada}
            )
        for codigo, nombre, simbolo in MONEDAS:
            Moneda.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre, "simbolo": simbolo})

        self.stdout.write(self.style.SUCCESS("Catálogos cargados."))
