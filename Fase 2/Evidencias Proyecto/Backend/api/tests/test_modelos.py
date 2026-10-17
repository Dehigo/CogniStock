from django.apps import apps
from django.db import IntegrityError, transaction
from django.test import TestCase

from api.models import Cotizacion, DetalleCotizacion, Entrada, EstadoCotizacion, Moneda, Movimiento, Producto, Proveedor, Rol, Stock, Usuario


class UsuarioTests(TestCase):
    def test_no_se_puede_crear_usuario_sin_rol(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(email="sinrol@cognistock.cl", password="x", nombre="Sin rol")

    def test_superusuario_queda_como_administrador(self):
        admin = Usuario.objects.create_superuser(email="admin@cognistock.cl", password="x", nombre="Admin")
        self.assertEqual(admin.rol.nombre, "Administrador")



class ModeloDatosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            email="encargado@cognistock.cl",
            password="clave-segura-123",
            nombre="Encargado",
            rol=Rol.objects.create(nombre="Encargado de inventario"),
        )
        cls.producto = Producto.objects.create(codigo="P-001", nombre="Producto de prueba")
        cls.cotizacion = Cotizacion.objects.create(
            proveedor=Proveedor.objects.create(nombre="Proveedor de prueba"),
            numero="COT-001",
            moneda=Moneda.objects.create(codigo="CLP", nombre="Peso chileno"),
            estado=EstadoCotizacion.objects.create(codigo="APROBADA", permite_entrada=True),
            creado_por=cls.usuario,
        )

    def test_el_modelo_tiene_30_tablas(self):
        self.assertEqual(len(list(apps.get_app_config("api").get_models())), 30)

    def test_el_stock_no_puede_quedar_negativo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Stock.objects.create(producto=self.producto, cantidad=-1)

    def test_detalle_de_cotizacion_con_cantidad_cero_falla(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DetalleCotizacion.objects.create(
                cotizacion=self.cotizacion,
                producto=self.producto,
                cantidad=0,
                precio_unitario=100,
            )

    def test_no_hay_entrada_sin_cotizacion(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Entrada.objects.create(usuario=self.usuario)

    def test_movimiento_de_entrada_sin_entrada_asociada_falla(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Movimiento.objects.create(
                producto=self.producto,
                usuario=self.usuario,
                tipo=Movimiento.Tipo.ENTRADA,
                cantidad=5,
            )

    def test_movimiento_de_entrada_valido(self):
        entrada = Entrada.objects.create(cotizacion=self.cotizacion, usuario=self.usuario)
        movimiento = Movimiento.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            tipo=Movimiento.Tipo.ENTRADA,
            cantidad=5,
            entrada=entrada,
        )
        self.assertEqual(movimiento.entrada, entrada)
