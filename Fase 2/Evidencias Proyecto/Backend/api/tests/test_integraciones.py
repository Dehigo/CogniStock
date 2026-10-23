import io
import json
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import Feriado, LlamadaApiExterna, Rol, TipoCambio, Usuario


def respuesta(datos):
    """Imita lo que devuelve urlopen: un archivo con JSON adentro."""
    return io.BytesIO(json.dumps(datos).encode())


FRANKFURTER = {"amount": 1.0, "base": "USD", "date": "2026-10-22", "rates": {"EUR": 0.89246}}
NAGER = [
    {"date": "2026-01-01", "localName": "Año Nuevo"},
    {"date": "2026-09-18", "localName": "Independencia Nacional"},
]


class IntegracionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_catalogos", verbosity=0)
        cls.usuario = Usuario.objects.create_user(
            email="u@c.cl", password="clave-segura-123", nombre="U", rol=Rol.objects.get(nombre="Usuario operativo")
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.usuario)

    def cambio(self, desde="USD", hacia="EUR"):
        return self.client.get("/api/integraciones/tipo-cambio/", {"desde": desde, "hacia": hacia})

    # CP-10: respuesta procesada
    def test_tipo_de_cambio(self):
        with mock.patch("api.integraciones.urlopen", return_value=respuesta(FRANKFURTER)) as api:
            r = self.cambio()
            r2 = self.cambio()  # la segunda vez se lee de la base
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.data["valor"], str(r.data["fecha"])), (0.89246, "2026-10-22"))
        self.assertEqual(r2.data["valor"], 0.89246)
        self.assertEqual(api.call_count, 1)
        self.assertTrue(LlamadaApiExterna.objects.get(servicio="FRANKFURTER").exito)

    # CP-10: error controlado
    def test_api_caida_usa_el_ultimo_valor_guardado(self):
        with mock.patch("api.integraciones.urlopen", return_value=respuesta(FRANKFURTER)):
            self.cambio()
        TipoCambio.objects.update(consultado_en="2026-01-01T00:00Z")  # ya no es de hoy
        with mock.patch("api.integraciones.urlopen", side_effect=TimeoutError("timeout")):
            r = self.cambio()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(LlamadaApiExterna.objects.filter(exito=False).exists())

    def test_api_caida_sin_valor_guardado(self):
        with mock.patch("api.integraciones.urlopen", side_effect=TimeoutError("timeout")):
            self.assertEqual(self.cambio().status_code, 503)

    def test_monedas_invalidas(self):
        self.assertEqual(self.cambio("USD", "CLP").status_code, 400)
        self.assertEqual(self.cambio("USD", "USD").status_code, 400)
        self.assertEqual(self.cambio("USD", "XYZ").status_code, 400)

    def test_feriados(self):
        with mock.patch("api.integraciones.urlopen", return_value=respuesta(NAGER)) as api:
            r = self.client.get("/api/integraciones/feriados/", {"anio": 2026})
            self.client.get("/api/integraciones/feriados/", {"anio": 2026})
        self.assertEqual([f["nombre"] for f in r.data], ["Año Nuevo", "Independencia Nacional"])
        self.assertEqual((api.call_count, Feriado.objects.count()), (1, 2))

    def test_feriados_api_caida(self):
        with mock.patch("api.integraciones.urlopen", side_effect=OSError("sin internet")):
            r = self.client.get("/api/integraciones/feriados/", {"anio": 2026})
        self.assertEqual(r.status_code, 503)
