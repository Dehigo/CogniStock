from django.core.cache import cache
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from api.models import BitacoraAuditoria, Rol, Usuario


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
