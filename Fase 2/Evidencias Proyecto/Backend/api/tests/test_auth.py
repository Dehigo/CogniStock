from django.core.cache import cache
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from api.models import BitacoraAuditoria, Rol, Usuario


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
