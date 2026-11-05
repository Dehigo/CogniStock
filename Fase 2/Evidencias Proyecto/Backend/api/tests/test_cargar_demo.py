from django.core.management import call_command
from django.test import TestCase

from api.models import AlertaStock, Cotizacion, Movimiento, Producto, Stock, Usuario


class CargarDemoTests(TestCase):
    def test_carga_datos_coherentes_y_no_duplica(self):
        call_command("cargar_demo", verbosity=0)
        call_command("cargar_demo", verbosity=0)  # la segunda vez no debe duplicar nada

        self.assertEqual(Producto.objects.count(), 10)
        self.assertEqual(Usuario.objects.count(), 3)
        self.assertTrue(Usuario.objects.get(email="vendedor@cognistock.cl").check_password("password"))
        estados = dict(Cotizacion.objects.values_list("numero", "estado__codigo"))
        self.assertEqual(estados, {"COT-2026-001": "RECIBIDA", "COT-2026-002": "APROBADA", "COT-2026-003": "REGISTRADA"})
        self.assertEqual(Stock.objects.get(producto__codigo="CLA-01").cantidad, 15)
        self.assertEqual(Movimiento.objects.count(), 7 + 5)  # 7 productos recibidos + 5 salidas
        self.assertTrue(AlertaStock.objects.filter(producto__codigo="CLA-01", estado="ACTIVA").exists())
