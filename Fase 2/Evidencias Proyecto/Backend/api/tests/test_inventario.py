from django.test import TestCase
from rest_framework.test import APIClient

from api.models import BitacoraAuditoria, CategoriaProducto, Producto, Proveedor, Rol, Stock, Usuario


class InventarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.encargado = Usuario.objects.create_user(
            email="encargado@cognistock.cl",
            password="clave-segura-123",
            nombre="Encargado",
            rol=Rol.objects.create(nombre=Rol.ENCARGADO),
        )
        cls.operativo = Usuario.objects.create_user(
            email="operativo@cognistock.cl",
            password="clave-segura-123",
            nombre="Operativo",
            rol=Rol.objects.create(nombre="Usuario operativo"),
        )
        cls.herramientas = CategoriaProducto.objects.create(nombre="Herramientas")
        cls.martillo = Producto.objects.create(codigo="MAR-01", nombre="Martillo", categoria=cls.herramientas)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)

    def crear_producto(self, **datos):
        base = {"codigo": "DES-01", "nombre": "Destornillador", "precio_referencia": 2500, "stock_minimo": 5}
        return self.client.post("/api/productos/", {**base, **datos}, format="json")

    def test_crear_categoria(self):
        respuesta = self.client.post("/api/categorias/", {"nombre": "Pinturas"}, format="json")

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="CATEGORIA_CREADA").exists())

    def test_no_se_repite_el_nombre_de_categoria(self):
        respuesta = self.client.post("/api/categorias/", {"nombre": "Herramientas"}, format="json")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data["nombre"], ["Ya existe una categoría con este nombre."])

    def test_desactivar_categoria(self):
        respuesta = self.client.delete(f"/api/categorias/{self.herramientas.id}/")

        self.assertEqual(respuesta.status_code, 204)
        self.herramientas.refresh_from_db()
        self.assertFalse(self.herramientas.activo)

    def test_crear_producto_tambien_crea_su_stock_en_cero(self):
        respuesta = self.crear_producto(categoria=self.herramientas.id)

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["stock_actual"], 0)
        self.assertEqual(respuesta.data["categoria_nombre"], "Herramientas")
        self.assertTrue(Stock.objects.filter(producto_id=respuesta.data["id"], cantidad=0).exists())

    def test_no_se_repite_el_codigo_de_producto(self):
        respuesta = self.crear_producto(codigo="MAR-01")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data["codigo"], ["Ya existe un producto con este código."])

    def test_no_se_aceptan_precios_ni_stock_minimo_negativos(self):
        respuesta = self.crear_producto(precio_referencia=-1, stock_minimo=-3)

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("precio_referencia", respuesta.data)
        self.assertIn("stock_minimo", respuesta.data)

    def test_no_se_aceptan_decimales_en_precio_ni_stock_minimo(self):
        respuesta = self.crear_producto(precio_referencia="1500.50", stock_minimo="2.5")

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("precio_referencia", respuesta.data)
        self.assertIn("stock_minimo", respuesta.data)

    def test_se_guarda_el_codigo_de_barras_del_envase(self):
        respuesta = self.crear_producto(codigo_qr="7801234567890")

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["codigo_qr"], "7801234567890")

    def test_sin_codigo_de_barras_se_genera_uno_interno(self):
        primero = self.crear_producto(codigo="A-1", codigo_qr="").data["codigo_qr"]
        segundo = self.crear_producto(codigo="A-2").data["codigo_qr"]

        self.assertTrue(primero.startswith("CS-"))
        self.assertNotEqual(primero, segundo)

    def test_no_se_repite_el_codigo_de_barras(self):
        self.crear_producto(codigo="A-1", codigo_qr="7801234567890")

        respuesta = self.crear_producto(codigo="A-2", codigo_qr="7801234567890")

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data["codigo_qr"], ["Ya existe un producto con este código de barras."])

    def test_buscar_y_filtrar_productos(self):
        self.crear_producto()

        por_codigo = self.client.get("/api/productos/", {"buscar": "mar-"})
        por_categoria = self.client.get("/api/productos/", {"categoria": self.herramientas.id})

        self.assertEqual([p["nombre"] for p in por_codigo.data], ["Martillo"])
        self.assertEqual([p["nombre"] for p in por_categoria.data], ["Martillo"])

    def test_editar_producto(self):
        respuesta = self.client.patch(f"/api/productos/{self.martillo.id}/", {"stock_minimo": 10}, format="json")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["stock_minimo"], 10)

    def test_desactivar_producto_no_lo_borra(self):
        respuesta = self.client.delete(f"/api/productos/{self.martillo.id}/")

        self.assertEqual(respuesta.status_code, 204)
        self.martillo.refresh_from_db()
        self.assertFalse(self.martillo.activo)

    def test_el_usuario_operativo_solo_puede_consultar(self):
        self.client.force_authenticate(self.operativo)

        self.assertEqual(self.client.get("/api/productos/").status_code, 200)
        self.assertEqual(self.crear_producto().status_code, 403)
        self.assertEqual(self.client.delete(f"/api/productos/{self.martillo.id}/").status_code, 403)

    def test_sin_sesion_no_se_puede_consultar(self):
        self.assertEqual(APIClient().get("/api/productos/").status_code, 401)


class ProveedoresTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.encargado = Usuario.objects.create_user(
            email="encargado@cognistock.cl",
            password="clave-segura-123",
            nombre="Encargado",
            rol=Rol.objects.create(nombre=Rol.ENCARGADO),
        )
        cls.proveedor = Proveedor.objects.create(nombre="TecnoChile", rut="76.123.456-7")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)

    def test_crear_proveedor(self):
        respuesta = self.client.post(
            "/api/proveedores/", {"nombre": "Distribuidora Sur", "email": "ventas@sur.cl"}, format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="PROVEEDOR_CREADO").exists())

    def test_email_invalido_se_rechaza(self):
        respuesta = self.client.post("/api/proveedores/", {"nombre": "X", "email": "no-es-email"}, format="json")

        self.assertEqual(respuesta.status_code, 400)

    def test_buscar_por_rut(self):
        respuesta = self.client.get("/api/proveedores/", {"buscar": "76.123"})

        self.assertEqual([p["nombre"] for p in respuesta.data], ["TecnoChile"])

    def test_desactivar_proveedor_no_lo_borra(self):
        self.assertEqual(self.client.delete(f"/api/proveedores/{self.proveedor.id}/").status_code, 204)
        self.proveedor.refresh_from_db()
        self.assertFalse(self.proveedor.activo)

