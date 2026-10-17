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


class GestionUsuariosTests(TestCase):
    URL = "/api/usuarios/"

    @classmethod
    def setUpTestData(cls):
        cls.rol_admin = Rol.objects.create(nombre=Rol.ADMINISTRADOR)
        cls.rol_operativo = Rol.objects.create(nombre="Usuario operativo")
        cls.admin = Usuario.objects.create_user(
            email="admin@cognistock.cl", password="clave-admin-123", nombre="Admin", rol=cls.rol_admin,
        )
        cls.operativo = Usuario.objects.create_user(
            email="pedro@cognistock.cl", password="clave-pedro-123", nombre="Pedro", rol=cls.rol_operativo,
        )

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def nuevo_usuario(self, **datos):
        base = {
            "nombre": "María",
            "email": "maria@cognistock.cl",
            "rol": self.rol_operativo.id,
            "password": "una-clave-segura-2026",
        }
        return self.client.post(self.URL, {**base, **datos}, format="json")

    def test_el_administrador_ve_la_lista_de_usuarios(self):
        respuesta = self.client.get(self.URL)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([u["email"] for u in respuesta.data], ["admin@cognistock.cl", "pedro@cognistock.cl"])
        self.assertEqual(respuesta.data[1]["rol_nombre"], "Usuario operativo")
        self.assertNotIn("password", respuesta.data[0])

    def test_un_usuario_que_no_es_administrador_no_puede_entrar(self):
        self.client.force_authenticate(self.operativo)

        self.assertEqual(self.client.get(self.URL).status_code, 403)
        self.assertEqual(self.nuevo_usuario().status_code, 403)

    def test_sin_sesion_responde_401(self):
        self.assertEqual(APIClient().get(self.URL).status_code, 401)

    def test_crear_usuario_y_que_pueda_iniciar_sesion(self):
        respuesta = self.nuevo_usuario()

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(respuesta.data["activo"])
        login = APIClient().post(
            "/api/auth/login/", {"email": "maria@cognistock.cl", "password": "una-clave-segura-2026"}, format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertTrue(
            BitacoraAuditoria.objects.filter(
                accion="USUARIO_CREADO", usuario=self.admin, entidad_id=respuesta.data["id"],
            ).exists()
        )

    def test_no_se_repiten_emails_aunque_cambien_mayusculas(self):
        respuesta = self.nuevo_usuario(email="PEDRO@cognistock.cl")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data["email"], ["Ya existe un usuario con este email."])

    def test_crear_sin_contrasena_falla(self):
        respuesta = self.nuevo_usuario(password="")

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.data)

    def test_no_se_aceptan_contrasenas_debiles(self):
        respuesta = self.nuevo_usuario(password="123")

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("password", respuesta.data)

    def test_rol_inexistente_falla(self):
        self.assertEqual(self.nuevo_usuario(rol=9999).status_code, 400)

    def test_editar_nombre_y_rol(self):
        respuesta = self.client.patch(
            f"{self.URL}{self.operativo.id}/", {"nombre": "Pedro Pérez", "rol": self.rol_admin.id}, format="json",
        )

        self.assertEqual(respuesta.status_code, 200)
        self.operativo.refresh_from_db()
        self.assertEqual(self.operativo.nombre, "Pedro Pérez")
        self.assertEqual(self.operativo.rol, self.rol_admin)

    def test_cambiar_contrasena_cierra_las_sesiones_del_usuario(self):
        Token.objects.create(user=self.operativo)

        respuesta = self.client.patch(
            f"{self.URL}{self.operativo.id}/", {"password": "nueva-clave-segura-2026"}, format="json",
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Token.objects.filter(user=self.operativo).exists())
        self.operativo.refresh_from_db()
        self.assertTrue(self.operativo.check_password("nueva-clave-segura-2026"))

    def test_desactivar_usuario(self):
        Token.objects.create(user=self.operativo)

        respuesta = self.client.delete(f"{self.URL}{self.operativo.id}/")

        self.assertEqual(respuesta.status_code, 204)
        self.operativo.refresh_from_db()
        self.assertFalse(self.operativo.is_active)
        self.assertTrue(Usuario.objects.filter(pk=self.operativo.pk).exists())
        self.assertFalse(Token.objects.filter(user=self.operativo).exists())
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="USUARIO_DESACTIVADO").exists())

    def test_reactivar_usuario(self):
        self.operativo.is_active = False
        self.operativo.save()

        respuesta = self.client.patch(f"{self.URL}{self.operativo.id}/", {"activo": True}, format="json")

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.data["activo"])

    def test_el_administrador_no_puede_desactivarse_a_si_mismo(self):
        self.assertEqual(self.client.delete(f"{self.URL}{self.admin.id}/").status_code, 400)
        respuesta = self.client.patch(f"{self.URL}{self.admin.id}/", {"activo": False}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_el_administrador_no_puede_cambiar_su_propio_rol(self):
        respuesta = self.client.patch(
            f"{self.URL}{self.admin.id}/", {"rol": self.rol_operativo.id}, format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_buscar_y_filtrar(self):
        self.operativo.is_active = False
        self.operativo.save()

        por_nombre = self.client.get(self.URL, {"buscar": "ped"})
        activos = self.client.get(self.URL, {"activo": "true"})

        self.assertEqual([u["email"] for u in por_nombre.data], ["pedro@cognistock.cl"])
        self.assertEqual([u["email"] for u in activos.data], ["admin@cognistock.cl"])

    def test_listar_roles(self):
        respuesta = self.client.get("/api/roles/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([r["nombre"] for r in respuesta.data], [Rol.ADMINISTRADOR, "Usuario operativo"])
