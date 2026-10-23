from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import Moneda, Producto, Proveedor, Rol, Stock, Usuario


class MovimientosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_catalogos", verbosity=0)
        cls.encargado = Usuario.objects.create_user(
            email="enc@cognistock.cl", password="clave-segura-123", nombre="Encargado",
            rol=Rol.objects.get(nombre=Rol.ENCARGADO))
        cls.operativo = Usuario.objects.create_user(
            email="op@cognistock.cl", password="clave-segura-123", nombre="Operativo",
            rol=Rol.objects.get(nombre="Usuario operativo"))

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)
        self.p = Producto.objects.create(codigo="MAR-01", codigo_qr="QR-MAR", nombre="Martillo", precio_referencia=1)
        Stock.objects.create(producto=self.p, cantidad=0)
        prov = Proveedor.objects.create(nombre="Prov")
        cid = self.client.post("/api/cotizaciones/", {
            "numero": "C-1", "proveedor": prov.id, "moneda": Moneda.objects.get(codigo="CLP").id,
            "detalles": [{"producto": self.p.id, "cantidad": 10, "precio_unitario": 1}]}, format="json").data["id"]
        self.client.post(f"/api/cotizaciones/{cid}/estado/", {"estado": "APROBADA"}, format="json")
        self.client.post("/api/entradas/", {"cotizacion": cid, "detalles": [{"producto": self.p.id, "cantidad": 10}]},
                         format="json")
        self.client.post("/api/salidas/", {"codigo_qr": "QR-MAR", "cantidad": 3}, format="json")

    def test_historial_completo(self):  # CP-09
        r = self.client.get("/api/movimientos/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m["tipo"] for m in r.data], ["SALIDA", "ENTRADA"])
        m = r.data[1]
        self.assertEqual((m["producto_nombre"], m["cantidad"], m["usuario_nombre"]), ("Martillo", 10, "Encargado"))
        self.assertIn("cotización C-1", m["referencia"])
        self.assertTrue(m["fecha"])

    def test_filtros(self):
        self.assertEqual(len(self.client.get("/api/movimientos/", {"tipo": "ENTRADA"}).data), 1)
        self.assertEqual(len(self.client.get("/api/movimientos/", {"buscar": "mar"}).data), 2)
        self.assertEqual(len(self.client.get("/api/movimientos/", {"desde": "2000-01-01", "hasta": "2000-01-02"}).data), 0)

    def test_solo_lectura_y_operativo_consulta(self):
        self.assertEqual(self.client.post("/api/movimientos/", {}, format="json").status_code, 405)
        self.client.force_authenticate(self.operativo)
        self.assertEqual(self.client.get("/api/movimientos/").status_code, 200)

    def test_fecha_imposible_se_ignora(self):
        r = self.client.get("/api/movimientos/", {"desde": "2026-13-45", "hasta": "abc"})
        self.assertEqual((r.status_code, len(r.data)), (200, 2))

    def test_resumen_de_inicio(self):
        r = self.client.get("/api/resumen/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.data["entradas_hoy"], r.data["salidas_hoy"], r.data["cotizaciones_por_aprobar"]), (1, 1, 0))
        self.assertEqual(r.data["cotizaciones_por_recibir"], 0)  # se recibió todo: quedó RECIBIDA
