from decimal import Decimal

from django.apps import apps
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from api.models import (
    BitacoraAuditoria,
    Cotizacion,
    DetalleCotizacion,
    Entrada,
    EstadoCotizacion,
    Moneda,
    Movimiento,
    Producto,
    Proveedor,
    Rol,
    Stock,
    Usuario,
)


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
            Stock.objects.create(producto=self.producto, cantidad=Decimal("-1"))

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


class LoginTests(TestCase):
    URL_LOGIN = "/api/auth/login/"
    URL_LOGOUT = "/api/auth/logout/"
    URL_ME = "/api/auth/me/"

    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            email="juan@cognistock.cl",
            password="clave-segura-123",
            nombre="Juan",
            rol=Rol.objects.create(nombre="Usuario operativo"),
        )

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def iniciar_sesion(self, email="juan@cognistock.cl", password="clave-segura-123"):
        return self.client.post(self.URL_LOGIN, {"email": email, "password": password}, format="json")

    def test_login_valido_entrega_token_y_datos_del_usuario(self):
        respuesta = self.iniciar_sesion()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["token"], Token.objects.get(user=self.usuario).key)
        self.assertEqual(
            respuesta.data["usuario"],
            {"id": self.usuario.id, "nombre": "Juan", "email": "juan@cognistock.cl", "rol": "Usuario operativo"},
        )
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="LOGIN", usuario=self.usuario).exists())

    def test_login_con_clave_incorrecta_se_rechaza(self):
        respuesta = self.iniciar_sesion(password="otra-clave")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data["detail"], "Email o contraseña incorrectos.")
        self.assertFalse(Token.objects.exists())
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="LOGIN_FALLIDO").exists())

    def test_email_inexistente_da_el_mismo_mensaje(self):
        respuesta = self.iniciar_sesion(email="nadie@cognistock.cl")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data["detail"], "Email o contraseña incorrectos.")

    def test_usuario_inactivo_no_puede_entrar(self):
        self.usuario.is_active = False
        self.usuario.save()

        self.assertEqual(self.iniciar_sesion().status_code, 400)

    def test_login_sin_datos_devuelve_errores_de_validacion(self):
        respuesta = self.client.post(self.URL_LOGIN, {}, format="json")

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("email", respuesta.data)
        self.assertIn("password", respuesta.data)

    def test_la_respuesta_nunca_incluye_la_contrasena(self):
        respuesta = self.iniciar_sesion()

        self.assertNotIn("password", respuesta.data["usuario"])

    def test_demasiados_intentos_seguidos_se_bloquean(self):
        for _ in range(10):
            self.iniciar_sesion(password="otra-clave")

        self.assertEqual(self.iniciar_sesion().status_code, 429)

    def test_me_sin_token_responde_401(self):
        self.assertEqual(self.client.get(self.URL_ME).status_code, 401)

    def test_me_con_token_devuelve_el_usuario(self):
        token = self.iniciar_sesion().data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        respuesta = self.client.get(self.URL_ME)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["email"], "juan@cognistock.cl")

    def test_logout_invalida_el_token(self):
        token = self.iniciar_sesion().data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        self.assertEqual(self.client.post(self.URL_LOGOUT).status_code, 204)
        self.assertEqual(self.client.get(self.URL_ME).status_code, 401)
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="LOGOUT", usuario=self.usuario).exists())

    def test_health_check_no_requiere_sesion(self):
        self.assertEqual(self.client.get("/api/health/").status_code, 200)

    def test_cors_permite_al_frontend_llamar_al_login(self):
        respuesta = self.client.options(
            self.URL_LOGIN,
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertEqual(respuesta.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
