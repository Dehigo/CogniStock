from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (BitacoraAuditoria, Cotizacion, Entrada, EstadoCotizacion, HistorialEstadoCotizacion,
                        Moneda, Movimiento, Producto, Proveedor, Rol, Stock, Usuario)


class CotizacionesEntradasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_catalogos", verbosity=0)
        cls.encargado = Usuario.objects.create_user(
            email="encargado@cognistock.cl", password="clave-segura-123", nombre="Encargado",
            rol=Rol.objects.get(nombre=Rol.ENCARGADO),
        )
        cls.operativo = Usuario.objects.create_user(
            email="operativo@cognistock.cl", password="clave-segura-123", nombre="Operativo",
            rol=Rol.objects.get(nombre="Usuario operativo"),
        )
        cls.proveedor = Proveedor.objects.create(nombre="Ferretería Sur")
        cls.clp = Moneda.objects.get(codigo="CLP")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)
        self.martillo = Producto.objects.create(codigo="MAR-01", codigo_qr="QR-MAR", nombre="Martillo",
                                                precio_referencia=5000, stock_minimo=2)
        self.clavo = Producto.objects.create(codigo="CLA-01", codigo_qr="QR-CLA", nombre="Clavos",
                                             precio_referencia=100, stock_minimo=10)
        Stock.objects.create(producto=self.martillo, cantidad=1)
        Stock.objects.create(producto=self.clavo, cantidad=0)

    def crear_cotizacion(self, **datos):
        base = {
            "numero": "COT-001", "proveedor": self.proveedor.id, "moneda": self.clp.id,
            "detalles": [
                {"producto": self.martillo.id, "cantidad": 10, "precio_unitario": "4500.00"},
                {"producto": self.clavo.id, "cantidad": 100, "precio_unitario": "80"},
            ],
        }
        return self.client.post("/api/cotizaciones/", {**base, **datos}, format="json")

    def aprobada(self):
        cid = self.crear_cotizacion().data["id"]
        r = self.client.post(f"/api/cotizaciones/{cid}/estado/", {"estado": "APROBADA"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        return cid

    def entrar(self, cid, detalles):
        return self.client.post("/api/entradas/", {"cotizacion": cid, "detalles": detalles}, format="json")

    def stock(self, producto):
        return Stock.objects.get(producto=producto).cantidad

    # CP-03
    def test_crear_cotizacion(self):
        r = self.crear_cotizacion()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["estado"], "REGISTRADA")
        self.assertEqual(r.data["total"], 53000.0)
        self.assertEqual(r.data["detalles"][0]["cantidad_pendiente"], 10)
        self.assertEqual(HistorialEstadoCotizacion.objects.count(), 1)

    def test_cotizacion_sin_detalle_o_repetida(self):
        self.assertEqual(self.crear_cotizacion(detalles=[]).status_code, 400)
        d = {"producto": self.martillo.id, "cantidad": 1, "precio_unitario": 1}
        self.assertEqual(self.crear_cotizacion(detalles=[d, d]).status_code, 400)
        self.assertEqual(self.crear_cotizacion(numero="X", detalles=[{**d, "cantidad": 0}]).status_code, 400)

    def test_numero_unico(self):
        self.crear_cotizacion()
        self.assertEqual(self.crear_cotizacion().status_code, 400)

    def test_editar_solo_registrada(self):
        cid = self.aprobada()
        r = self.client.patch(f"/api/cotizaciones/{cid}/", {"observaciones": "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_transiciones(self):
        cid = self.crear_cotizacion().data["id"]
        r = self.client.post(f"/api/cotizaciones/{cid}/estado/", {"estado": "RECIBIDA"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.client.post(f"/api/cotizaciones/{cid}/estado/", {"estado": "ANULADA"}, format="json")
        r = self.client.post(f"/api/cotizaciones/{cid}/estado/", {"estado": "APROBADA"}, format="json")
        self.assertEqual((r.status_code, r.data["resultado"]), (409, "TRANSICION_INVALIDA"))

    # CP-04
    def test_entrada_sin_cotizacion(self):
        r = self.client.post("/api/entradas/", {"detalles": [{"producto": self.martillo.id, "cantidad": 1}]},
                             format="json")
        self.assertEqual((r.status_code, r.data["resultado"]), (400, "COTIZACION_REQUERIDA"))
        self.assertEqual(self.stock(self.martillo), 1)
        self.assertFalse(Entrada.objects.exists())

    def test_entrada_con_cotizacion_no_aprobada(self):
        cid = self.crear_cotizacion().data["id"]
        r = self.entrar(cid, [{"producto": self.martillo.id, "cantidad": 1}])
        self.assertEqual((r.status_code, r.data["resultado"]), (409, "COTIZACION_NO_VALIDA"))
        self.assertEqual(self.stock(self.martillo), 1)
        self.assertTrue(BitacoraAuditoria.objects.filter(accion="ENTRADA_RECHAZADA_COTIZACION_NO_VALIDA").exists())

    def test_entrada_cotizacion_inexistente(self):
        r = self.entrar(9999, [{"producto": self.martillo.id, "cantidad": 1}])
        self.assertEqual(r.status_code, 404)

    # CP-05
    def test_entrada_valida_suma_stock_y_genera_movimientos(self):
        cid = self.aprobada()
        r = self.entrar(cid, [{"producto": self.martillo.id, "cantidad": 4}, {"producto": self.clavo.id, "cantidad": 50}])
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.stock(self.martillo), 5)
        self.assertEqual(self.stock(self.clavo), 50)
        movs = Movimiento.objects.filter(tipo="ENTRADA")
        self.assertEqual(movs.count(), 2)
        self.assertTrue(all(m.usuario == self.encargado and m.entrada_id for m in movs))
        self.assertEqual(Cotizacion.objects.get(pk=cid).estado.codigo, "APROBADA")

    def test_entradas_parciales_y_cierre_automatico(self):
        cid = self.aprobada()
        self.entrar(cid, [{"producto": self.martillo.id, "cantidad": 10}])
        r = self.entrar(cid, [{"producto": self.clavo.id, "cantidad": 101}])
        self.assertEqual((r.status_code, r.data["resultado"], r.data["pendiente"]), (409, "EXCEDE_COTIZADO", 100))
        r = self.entrar(cid, [{"producto": self.martillo.id, "cantidad": 1}])
        self.assertEqual(r.data["resultado"], "EXCEDE_COTIZADO")
        r = self.entrar(cid, [{"producto": self.clavo.id, "cantidad": 100}])
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Cotizacion.objects.get(pk=cid).estado.codigo, "RECIBIDA")
        r = self.entrar(cid, [{"producto": self.clavo.id, "cantidad": 1}])
        self.assertEqual(r.data["resultado"], "COTIZACION_NO_VALIDA")
        detalle = self.client.get(f"/api/cotizaciones/{cid}/").data["detalles"]
        self.assertEqual([d["cantidad_pendiente"] for d in detalle], [0, 0])

    def test_producto_no_cotizado(self):
        cid = self.aprobada()
        otro = Producto.objects.create(codigo="OTR", codigo_qr="QR-OTR", nombre="Otro", precio_referencia=1)
        r = self.entrar(cid, [{"producto": otro.id, "cantidad": 1}])
        self.assertEqual(r.data["resultado"], "PRODUCTO_NO_COTIZADO")

    def test_cantidad_invalida_no_cambia_nada(self):
        cid = self.aprobada()
        r = self.entrar(cid, [{"producto": self.martillo.id, "cantidad": 2}, {"producto": self.clavo.id, "cantidad": 0}])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.stock(self.martillo), 1)
        self.assertFalse(Movimiento.objects.exists())

    def test_operativo_no_registra(self):
        cid = self.aprobada()
        self.client.force_authenticate(self.operativo)
        self.assertEqual(self.entrar(cid, [{"producto": self.martillo.id, "cantidad": 1}]).status_code, 403)
        self.assertEqual(self.crear_cotizacion(numero="COT-9").status_code, 403)
        self.assertEqual(self.client.get("/api/cotizaciones/").status_code, 200)

    def test_catalogos_idempotentes(self):
        call_command("cargar_catalogos", verbosity=0)
        self.assertEqual(EstadoCotizacion.objects.count(), 4)
        self.assertTrue(EstadoCotizacion.objects.get(codigo="APROBADA").permite_entrada)

    def test_datos_mal_formados(self):
        cid = self.aprobada()
        for cuerpo in ({"cotizacion": "abc", "detalles": [{"producto": self.martillo.id, "cantidad": 1}]},
                       {"cotizacion": cid, "detalles": "martillo"},
                       {"cotizacion": cid, "detalles": ["x"]},
                       {"cotizacion": cid, "detalles": [{"producto": "abc", "cantidad": 1}]}):
            r = self.client.post("/api/entradas/", cuerpo, format="json")
            self.assertIn(r.status_code, (400, 409), cuerpo)
        self.assertEqual(self.stock(self.martillo), 1)
