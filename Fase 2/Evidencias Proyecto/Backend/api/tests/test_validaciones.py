from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import CategoriaProducto, EscaneoQR, Moneda, Producto, Proveedor, Rol, Stock, Usuario


class ValidacionesFormulariosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_catalogos", verbosity=0)
        cls.admin = Usuario.objects.create_user(
            email="admin@cognistock.cl", password="clave-segura-123", nombre="Admin",
            rol=Rol.objects.get(nombre=Rol.ADMINISTRADOR),
        )
        cls.encargado = Usuario.objects.create_user(
            email="encargado@cognistock.cl", password="clave-segura-123", nombre="Encargado",
            rol=Rol.objects.get(nombre=Rol.ENCARGADO),
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)

    def post(self, url, datos):
        return self.client.post(url, datos, format="json")

    def test_rut_proveedor(self):
        r = self.post("/api/proveedores/", {"nombre": "Ferretería Sur", "rut": "76.123.456-0"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["rut"], "76123456-0")  # se guarda sin puntos

        self.assertEqual(self.post("/api/proveedores/", {"nombre": "Otro", "rut": "76123456-0"}).status_code, 400)
        self.assertEqual(self.post("/api/proveedores/", {"nombre": "Otro", "rut": "76123456-5"}).status_code, 400)
        self.assertEqual(self.post("/api/proveedores/", {"nombre": "Otro", "rut": "hola"}).status_code, 400)
        self.assertEqual(self.post("/api/proveedores/", {"nombre": "Sin RUT"}).status_code, 201)

    def test_telefono_proveedor(self):
        self.assertEqual(self.post("/api/proveedores/", {"nombre": "A", "telefono": "+56 9 1234 5678"}).status_code, 201)
        self.assertEqual(self.post("/api/proveedores/", {"nombre": "B", "telefono": "llamar"}).status_code, 400)
        self.assertEqual(self.post("/api/proveedores/", {"nombre": "C", "telefono": "123"}).status_code, 400)

    def test_codigos_de_producto_sin_espacios_ni_simbolos(self):
        self.assertEqual(self.post("/api/productos/", {"codigo": "MAR 01", "nombre": "Martillo"}).status_code, 400)
        self.assertEqual(self.post("/api/productos/", {"codigo": "MAR-01", "nombre": "Martillo",
                                                       "codigo_qr": "<script>"}).status_code, 400)
        self.assertEqual(self.post("/api/productos/", {"codigo": "MAR-01", "nombre": "Martillo"}).status_code, 201)

    def test_categoria_inactiva_no_se_asigna(self):
        inactiva = CategoriaProducto.objects.create(nombre="Antigua", activo=False)
        r = self.post("/api/productos/", {"codigo": "X-1", "nombre": "X", "categoria": inactiva.id})
        self.assertEqual(r.status_code, 400)

        # Un producto que ya la tenía puede editarse sin cambiarla.
        producto = Producto.objects.create(codigo="Y-1", nombre="Y", categoria=inactiva)
        r = self.client.patch(f"/api/productos/{producto.id}/", {"nombre": "Y2", "categoria": inactiva.id}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_cotizacion_con_fecha_futura(self):
        producto = Producto.objects.create(codigo="Z-1", nombre="Z")
        datos = {
            "numero": "COT-1", "proveedor": Proveedor.objects.create(nombre="P").id,
            "moneda": Moneda.objects.get(codigo="CLP").id,
            "fecha": str(timezone.localdate() + timedelta(days=1)),
            "detalles": [{"producto": producto.id, "cantidad": 1, "precio_unitario": "10"}],
        }
        self.assertEqual(self.post("/api/cotizaciones/", datos).status_code, 400)
        self.assertEqual(self.post("/api/cotizaciones/", {**datos, "fecha": str(timezone.localdate())}).status_code, 201)

    def test_salida_con_observaciones_largas_o_qr_muy_largo(self):
        producto = Producto.objects.create(codigo="W-1", codigo_qr="QR-W", nombre="W")
        Stock.objects.create(producto=producto, cantidad=5)

        r = self.post("/api/salidas/", {"codigo_qr": "QR-W", "cantidad": 1, "observaciones": "x" * 501})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Stock.objects.get(producto=producto).cantidad, 5)

        # Un QR más largo que el campo se rechaza como desconocido sin romper el registro del escaneo.
        r = self.post("/api/salidas/", {"codigo_qr": "Q" * 300, "cantidad": 1})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(EscaneoQR.objects.get().resultado, "QR_INVALIDO")

    def test_clave_de_parametro(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.post("/api/parametros/", {"clave": "Días cobertura", "valor": "7"}).status_code, 400)
        self.assertEqual(self.post("/api/parametros/", {"clave": "dias_cobertura", "valor": "7"}).status_code, 201)
