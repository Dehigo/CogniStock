from unittest import mock

from django.test import TestCase, override_settings
from langchain_core.messages import AIMessage
from rest_framework.test import APIClient

from api import agente
from api.models import (ConversacionAgente, EjecucionToolAgente, LlamadaApiExterna, Movimiento, Producto,
                        RecomendacionReposicion, Rol, Stock, Usuario)


class ModeloFalso:
    """Devuelve respuestas preparadas, como lo haría Groq."""
    model_name = "falso"

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.recibidos = []

    def bind_tools(self, tools):
        self.tools = [t.name for t in tools]
        return self

    def invoke(self, mensajes):
        self.recibidos.append(list(mensajes))
        return self.respuestas.pop(0)


def llamada(nombre, args, id_="1"):
    return AIMessage(content="", tool_calls=[{"name": nombre, "args": args, "id": id_}])


class AgenteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.encargado = Usuario.objects.create_user(email="e@c.cl", password="clave-segura-123", nombre="Enc",
                                                    rol=Rol.objects.create(nombre=Rol.ENCARGADO))
        cls.operativo = Usuario.objects.create_user(email="o@c.cl", password="clave-segura-123", nombre="Op",
                                                    rol=Rol.objects.create(nombre="Usuario operativo"))
        cls.martillo = Producto.objects.create(codigo="MAR-01", codigo_qr="QR-M", nombre="Martillo",
                                               precio_referencia=1, stock_minimo=5)
        Stock.objects.create(producto=cls.martillo, cantidad=2)
        cls.clavo = Producto.objects.create(codigo="CLA-01", codigo_qr="QR-C", nombre="Clavo",
                                            precio_referencia=1, stock_minimo=1)
        Stock.objects.create(producto=cls.clavo, cantidad=50)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.encargado)

    def preguntar(self, modelo, pregunta="¿Qué productos tienen stock bajo?"):
        with mock.patch.object(agente, "crear_modelo", return_value=modelo):
            return self.client.post("/api/agente/consultar/", {"pregunta": pregunta}, format="json")

    def test_consulta_con_tool_de_lectura(self):  # CP-11
        modelo = ModeloFalso([llamada("productos_stock_bajo", {}), AIMessage(content="Martillo: 2 de 5.")])
        r = self.preguntar(modelo)
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["respuesta"], "Martillo: 2 de 5.")
        self.assertEqual(r.data["herramientas"], [{"tool": "productos_stock_bajo", "permitido": True}])
        resultado = EjecucionToolAgente.objects.get().resultado
        self.assertEqual([p["codigo"] for p in resultado], ["MAR-01"])
        self.assertIn("MAR-01", modelo.recibidos[1][-1].content)
        self.assertEqual(LlamadaApiExterna.objects.filter(servicio="GROQ", exito=True).count(), 2)
        self.assertEqual(ConversacionAgente.objects.get().usuario, self.encargado)

    def test_solo_tools_permitidas(self):  # CA-06
        modelo = ModeloFalso([llamada("registrar_salida", {"codigo_qr": "QR-M", "cantidad": 2}),
                              AIMessage(content="No puedo hacer eso.")])
        self.preguntar(modelo, "Saca 2 martillos")
        self.assertEqual(sorted(modelo.tools), ["buscar_productos", "productos_stock_bajo",
                                                "proponer_reposicion", "ultimos_movimientos"])
        ejecucion = EjecucionToolAgente.objects.get()
        self.assertFalse(ejecucion.permitido)
        self.assertEqual(Stock.objects.get(producto=self.martillo).cantidad, 2)
        self.assertFalse(Movimiento.objects.exists())

    def test_propuesta_requiere_confirmacion_humana(self):  # RB-007
        modelo = ModeloFalso([llamada("proponer_reposicion", {"codigo_producto": "MAR-01", "cantidad": 10,
                                                              "justificacion": "Bajo el mínimo"}),
                              AIMessage(content="Propuse reponer 10.")])
        r = self.preguntar(modelo, "¿Conviene reponer martillos?")
        self.assertEqual(len(r.data["propuestas"]), 1)
        rec = RecomendacionReposicion.objects.get()
        self.assertEqual((rec.estado, rec.cantidad_sugerida), ("PROPUESTA", 10))
        self.assertEqual(Stock.objects.get(producto=self.martillo).cantidad, 2)

        self.client.force_authenticate(self.operativo)
        self.assertEqual(self.client.post(f"/api/recomendaciones/{rec.id}/revisar/", {"estado": "ACEPTADA"},
                                          format="json").status_code, 403)
        self.client.force_authenticate(self.encargado)
        r = self.client.post(f"/api/recomendaciones/{rec.id}/revisar/", {"estado": "ACEPTADA"}, format="json")
        self.assertEqual((r.status_code, r.data["estado"], r.data["revisada_por_nombre"]), (200, "ACEPTADA", "Enc"))
        r = self.client.post(f"/api/recomendaciones/{rec.id}/revisar/", {"estado": "DESCARTADA"}, format="json")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Stock.objects.get(producto=self.martillo).cantidad, 2)

    def test_tools_directas(self):
        self.assertEqual([p["codigo"] for p in agente.buscar_productos.invoke({"texto": "cla"})], ["CLA-01"])
        self.assertIn("error", agente.proponer_reposicion.invoke(
            {"codigo_producto": "NO", "cantidad": 1, "justificacion": ""}))

    @override_settings(GROQ_API_KEY="")
    def test_sin_clave_responde_503(self):
        r = self.client.post("/api/agente/consultar/", {"pregunta": "hola"}, format="json")
        self.assertEqual(r.status_code, 503)
        self.assertIn("GROQ_API_KEY", r.data["detail"])

    def test_error_de_groq_queda_registrado(self):
        class Caido(ModeloFalso):
            def invoke(self, mensajes):
                raise TimeoutError("timeout")
        r = self.preguntar(Caido([]))
        self.assertEqual(r.status_code, 503)
        self.assertTrue(LlamadaApiExterna.objects.filter(servicio="GROQ", exito=False).exists())

    def test_pregunta_vacia_o_larga(self):
        self.assertEqual(self.client.post("/api/agente/consultar/", {"pregunta": " "}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/agente/consultar/", {"pregunta": "x" * 501},
                                          format="json").status_code, 400)

    def test_operativo_puede_consultar(self):
        self.client.force_authenticate(self.operativo)
        r = self.preguntar(ModeloFalso([AIMessage(content="Hola")]), "hola")
        self.assertEqual(r.status_code, 200)
