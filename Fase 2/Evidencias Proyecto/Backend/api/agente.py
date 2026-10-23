"""Agente IA de inventario (RF-11) con LangChain + Groq.

El agente solo usa las tools de TOOLS: consultan datos o proponen una reposición que una persona
debe aceptar. Ninguna tool cambia stock ni registra entradas o salidas (RB-007, RNF-08).
Cada tool usada queda en ejecuciones_tool_agente y cada llamada a Groq en llamadas_api_externa.
"""

import time

from django.conf import settings
from django.db.models import F, Q
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from api.models import (
    ConversacionAgente,
    EjecucionToolAgente,
    LlamadaApiExterna,
    Movimiento,
    Producto,
    RecomendacionReposicion,
)

MAX_PASOS = 4  # máximo de idas y vueltas con el modelo por pregunta
LIMITE_RESULTADOS = 15

INSTRUCCIONES = """Eres el asistente de inventario de CogniStock. Respondes en español, breve y con datos concretos.
Escribe en texto plano, sin Markdown ni tablas: usa frases cortas o líneas que empiecen con "- ".
Usa siempre las herramientas para obtener datos; nunca inventes productos, cantidades ni fechas.
No puedes registrar entradas, salidas ni cambiar stock. Si te lo piden, explica que debe hacerlo una persona
desde la pantalla correspondiente. Si conviene reponer un producto, usa proponer_reposicion: la propuesta
queda pendiente hasta que un encargado la acepte."""


class AgenteNoDisponible(Exception):
    pass


def _producto(producto):
    stock = getattr(producto, "stock", None)  # None si el producto aún no tiene fila de stock
    return {
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "categoria": producto.categoria.nombre if producto.categoria else None,
        "stock_actual": stock.cantidad if stock else 0,
        "stock_minimo": producto.stock_minimo,
        "activo": producto.activo,
    }


@tool
def buscar_productos(texto: str) -> list:
    """Busca productos por nombre o código y devuelve su stock actual y mínimo."""
    productos = Producto.objects.select_related("categoria", "stock").order_by("nombre")
    productos = productos.filter(Q(nombre__icontains=texto) | Q(codigo__icontains=texto))
    return [_producto(p) for p in productos[:LIMITE_RESULTADOS]]


@tool
def productos_stock_bajo() -> list:
    """Lista los productos activos cuyo stock está bajo su stock mínimo, del más crítico al menos crítico."""
    productos = Producto.objects.select_related("categoria", "stock").order_by("stock__cantidad")
    productos = productos.filter(activo=True, stock__cantidad__lt=F("stock_minimo"))
    return [_producto(p) for p in productos[:LIMITE_RESULTADOS]]


@tool
def ultimos_movimientos(codigo_producto: str = "", limite: int = 10) -> list:
    """Devuelve las últimas entradas y salidas, opcionalmente de un producto por su código."""
    movimientos = Movimiento.objects.select_related("producto", "usuario").order_by("-fecha")
    if codigo_producto:
        movimientos = movimientos.filter(producto__codigo__iexact=codigo_producto)
    limite = max(1, min(int(limite), LIMITE_RESULTADOS))
    return [
        {
            "fecha": m.fecha.isoformat(timespec="minutes"),
            "tipo": m.tipo,
            "producto": m.producto.nombre,
            "cantidad": m.cantidad,
            "usuario": m.usuario.nombre,
        }
        for m in movimientos[:limite]
    ]


@tool
def proponer_reposicion(codigo_producto: str, cantidad: int, justificacion: str) -> dict:
    """Propone reponer un producto. No compra ni cambia stock: crea una propuesta que un encargado acepta o descarta."""
    # Solo valida. La propuesta se guarda en _ejecutar_tool, que conoce la conversación.
    producto = Producto.objects.filter(codigo__iexact=codigo_producto, activo=True).first()
    if producto is None:
        return {"error": f"No existe un producto activo con código {codigo_producto}."}
    if int(cantidad) <= 0:
        return {"error": "La cantidad sugerida debe ser mayor que 0."}
    return {"producto_id": producto.id, "producto": producto.nombre, "cantidad": int(cantidad), "justificacion": justificacion}


TOOLS = {t.name: t for t in (buscar_productos, productos_stock_bajo, ultimos_movimientos, proponer_reposicion)}


def crear_modelo():
    if not settings.GROQ_API_KEY:
        raise AgenteNoDisponible("El agente no está configurado: falta GROQ_API_KEY en el .env del backend.")
    return ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY, temperature=0, timeout=30)


def _invocar(modelo, mensajes, usuario):
    """Llama a Groq y deja registrada la llamada, haya funcionado o no."""
    inicio = time.monotonic()
    respuesta, error = None, None
    try:
        respuesta = modelo.invoke(mensajes)
    except Exception as e:
        error = e

    LlamadaApiExterna.objects.create(
        servicio="GROQ",
        endpoint="chat/completions",
        metodo="POST",
        estado_http=None if error else 200,
        exito=error is None,
        mensaje_error=str(error or "")[:500],
        duracion_ms=int((time.monotonic() - inicio) * 1000),
        usuario=usuario,
    )
    if error:
        raise AgenteNoDisponible("El servicio de IA no respondió. Intenta de nuevo en unos minutos.") from error
    return respuesta


def _ejecutar_tool(conversacion, llamada):
    nombre, argumentos = llamada["name"], llamada.get("args") or {}
    if nombre not in TOOLS:  # el modelo pidió algo fuera de la lista: se rechaza y queda registrado (CA-06)
        EjecucionToolAgente.objects.create(
            conversacion=conversacion, tool=nombre[:80], parametros=argumentos, permitido=False, motivo_rechazo="Tool no permitida."
        )
        return {"error": f"La herramienta {nombre} no está permitida."}

    try:
        resultado = TOOLS[nombre].invoke(argumentos)
    except Exception as error:
        resultado = {"error": f"No se pudo ejecutar {nombre}: {error}"}

    if nombre == "proponer_reposicion" and "error" not in resultado:
        recomendacion = RecomendacionReposicion.objects.create(
            producto_id=resultado["producto_id"],
            cantidad_sugerida=resultado["cantidad"],
            justificacion=resultado["justificacion"] or "Propuesta del agente.",
            conversacion=conversacion,
        )
        resultado = {**resultado, "recomendacion_id": recomendacion.id, "estado": "PROPUESTA"}

    EjecucionToolAgente.objects.create(
        conversacion=conversacion, tool=nombre, parametros=argumentos, resultado=resultado, permitido=True
    )
    return resultado


def consultar(usuario, pregunta, modelo=None):
    """Responde una pregunta usando solo las tools permitidas. Devuelve la ConversacionAgente guardada."""
    modelo = modelo or crear_modelo()
    conversacion = ConversacionAgente.objects.create(usuario=usuario, pregunta=pregunta, modelo=modelo.model_name)
    con_tools = modelo.bind_tools(list(TOOLS.values()))
    mensajes = [SystemMessage(INSTRUCCIONES), HumanMessage(pregunta)]
    tokens = 0

    # Se repite: el modelo pide herramientas, se las damos, y así hasta que responde con texto.
    for _ in range(MAX_PASOS):
        respuesta = _invocar(con_tools, mensajes, usuario)
        tokens += (respuesta.usage_metadata or {}).get("total_tokens", 0)
        mensajes.append(respuesta)
        if not respuesta.tool_calls:
            conversacion.respuesta = respuesta.content
            break
        for llamada in respuesta.tool_calls:
            resultado = _ejecutar_tool(conversacion, llamada)
            mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))
    else:
        conversacion.respuesta = "No pude completar la consulta. Prueba con una pregunta más específica."

    conversacion.tokens_usados = tokens or None
    conversacion.save(update_fields=["respuesta", "tokens_usados"])
    return conversacion
