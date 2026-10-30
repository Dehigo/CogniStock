"""APIs externas (RF-10): Frankfurter (tipo de cambio), Nager.Date (feriados de Chile)
y UPCitemdb (datos de un producto según su código de barras).

Regla RB-008: si una API falla, la app no se cae. Cada llamada tiene un tiempo máximo,
queda registrada en llamadas_api_externa y los datos se guardan para no pedirlos de nuevo.
"""

import json
import time
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from api.models import Feriado, LlamadaApiExterna, Moneda, TipoCambio

SEGUNDOS_MAXIMOS = 5


class ApiNoDisponible(Exception):
    pass


def _pedir(servicio, url, usuario):
    """Hace un GET, registra la llamada y devuelve el JSON. Si falla, lanza ApiNoDisponible."""
    inicio = time.monotonic()
    datos, error = None, None
    try:
        # Algunas APIs rechazan (403) a quien no dice quién es, por eso se envía un User-Agent.
        with urlopen(Request(url, headers={"User-Agent": "CogniStock/1.0"}), timeout=SEGUNDOS_MAXIMOS) as respuesta:
            datos = json.load(respuesta)
    except Exception as e:  # sin internet, timeout, error HTTP o respuesta que no es JSON
        error = e

    LlamadaApiExterna.objects.create(
        servicio=servicio,
        endpoint=url[:500],
        exito=error is None,
        estado_http=getattr(error, "code", None) if error else 200,
        mensaje_error=str(error or "")[:500],
        duracion_ms=int((time.monotonic() - inicio) * 1000),
        usuario=usuario,
    )
    if error:
        raise ApiNoDisponible(f"{servicio} no respondió.") from error
    return datos


def tipo_de_cambio(desde, hacia, usuario):
    """Cuánto vale 1 unidad de `desde` en `hacia` (por ejemplo USD → EUR). Devuelve un TipoCambio."""
    origen = Moneda.objects.get(codigo=desde)
    destino = Moneda.objects.get(codigo=hacia)
    guardados = TipoCambio.objects.filter(moneda_origen=origen, moneda_destino=destino).order_by("-fecha")

    # Si ya se consultó hoy, no se vuelve a pedir.
    de_hoy = guardados.filter(consultado_en__date=timezone.localdate()).first()
    if de_hoy:
        return de_hoy

    try:
        datos = _pedir("FRANKFURTER", f"{settings.FRANKFURTER_BASE_URL}/latest?from={desde}&to={hacia}", usuario)
        return TipoCambio.objects.update_or_create(
            moneda_origen=origen, moneda_destino=destino, fecha=datos["date"], defaults={"valor": datos["rates"][hacia]}
        )[0]
    except (ApiNoDisponible, KeyError):
        # Respuesta degradada: si la API falla, se usa el último valor guardado.
        ultimo = guardados.first()
        if ultimo is None:
            raise ApiNoDisponible("No se pudo obtener el tipo de cambio y no hay uno guardado.")
        return ultimo


def feriados(anio, usuario):
    """Feriados de Chile del año. Se piden una vez a Nager.Date y luego se leen de la base."""
    guardados = Feriado.objects.filter(pais="CL", fecha__year=anio).order_by("fecha")
    if guardados.exists():
        return list(guardados)

    datos = _pedir("NAGER_DATE", f"{settings.NAGER_DATE_BASE_URL}/PublicHolidays/{anio}/CL", usuario)
    for feriado in datos:
        Feriado.objects.get_or_create(fecha=feriado["date"], pais="CL", defaults={"nombre": feriado["localName"][:150]})
    return list(guardados)



def buscar_producto(codigo_barras, usuario):
    """Nombre, marca y categoría de un código de barras según UPCitemdb, o None si no lo conoce."""
    datos = _pedir("PRODUCTOS", f"{settings.PRODUCTOS_API_BASE_URL}/lookup?upc={codigo_barras}", usuario)
    if not datos.get("items"):
        return None
    item = datos["items"][0]
    return {"nombre": item.get("title", ""), "marca": item.get("brand", ""), "categoria": item.get("category", "")}
