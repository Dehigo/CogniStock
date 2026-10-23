from django.test import TestCase
from rest_framework.test import APIClient

from api.models import AlertaStock, BitacoraAuditoria, EscaneoQR, Movimiento, Producto, Rol, Salida, Stock, Usuario


class SalidasQrTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.encargado = Usuario.objects.create_user(
            email="encargado@cognistock.cl", password="clave-segura-123", nombre="Encargado",
            rol=Rol.objects.create(nombre=Rol.ENCARGADO),
        )
        cls.operativo = Usuario.objects.create_user(
            email="operativo@cognistock.cl", password="clave-segura-123", nombre="Operativo",
            rol=Rol.objects.create(nombre="Operativo"),
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)
        self.producto = Producto.objects.create(codigo="DES-01", codigo_qr="QR-DES-01", nombre="Destornillador",
                                                precio_referencia=2500, stock_minimo=5)
        Stock.objects.create(producto=self.producto, cantidad=10)

    def salir(self, **datos):
        base = {"codigo_qr": "QR-DES-01", "cantidad": 3}
        return self.client.post("/api/salidas/", {**base, **datos}, format="json")

    def test_consultar_por_qr(self):
        r = self.client.get("/api/productos/qr/", {"codigo_qr": "QR-DES-01"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["stock_actual"], 10)

    def test_consultar_qr_desconocido(self):
        r = self.client.get("/api/productos/qr/", {"codigo_qr": "NO-EXISTE"})
        self.assertEqual(r.status_code, 404)

    def test_salida_valida_resta_stock_y_genera_movimiento(self):  # CP-07
        r = self.salir()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["stock_restante"], 7)
        self.assertEqual(Stock.objects.get(producto=self.producto).cantidad, 7)
        mov = Movimiento.objects.get()
        self.assertEqual((mov.tipo, mov.cantidad, mov.usuario), ("SALIDA", 3, self.encargado))
        self.assertEqual(EscaneoQR.objects.get().resultado, "OK")
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="SALIDA_REGISTRADA").exists())

    def test_stock_insuficiente_no_cambia_nada(self):  # CP-08
        r = self.salir(cantidad=11)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["resultado"], "SIN_STOCK")
        self.assertEqual(Stock.objects.get(producto=self.producto).cantidad, 10)
        self.assertFalse(Salida.objects.exists())
        self.assertFalse(Movimiento.objects.exists())
        self.assertEqual(EscaneoQR.objects.get().resultado, "SIN_STOCK")

    def test_qr_desconocido(self):
        r = self.salir(codigo_qr="NO-EXISTE")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(EscaneoQR.objects.get().resultado, "QR_INVALIDO")

    def test_producto_inactivo(self):
        self.producto.activo = False
        self.producto.save()
        r = self.salir()
        self.assertEqual((r.status_code, r.data["resultado"]), (409, "PRODUCTO_INACTIVO"))

    def test_cantidad_invalida(self):
        for cantidad in (0, -1, "abc", 2.5, None):
            r = self.salir(cantidad=cantidad)
            self.assertEqual((r.status_code, r.data["resultado"]), (400, "CANTIDAD_INVALIDA"), cantidad)
        self.assertEqual(Stock.objects.get(producto=self.producto).cantidad, 10)

    def test_alerta_stock_bajo(self):
        self.salir(cantidad=6)
        self.assertEqual(AlertaStock.objects.get().tipo, "STOCK_BAJO")

    def test_operativo_no_registra_salidas(self):
        self.client.force_authenticate(self.operativo)
        self.assertEqual(self.salir().status_code, 403)
