from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api import integraciones
from api.models import Moneda


@api_view(["GET"])
def tipo_de_cambio(request):
    """GET /api/integraciones/tipo-cambio/?desde=USD&hacia=EUR"""
    desde = request.query_params.get("desde", "").upper()
    hacia = request.query_params.get("hacia", "").upper()
    if "CLP" in (desde, hacia):
        mensaje = "Frankfurter no publica el peso chileno (CLP); solo convierte entre monedas como USD y EUR."
        return Response({"detail": mensaje}, status=status.HTTP_400_BAD_REQUEST)
    if desde == hacia or Moneda.objects.filter(codigo__in=[desde, hacia]).count() != 2:
        return Response({"detail": "Indica dos monedas distintas del catálogo."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cambio = integraciones.tipo_de_cambio(desde, hacia, request.user)
    except integraciones.ApiNoDisponible as error:
        return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    datos = {"desde": desde, "hacia": hacia, "valor": float(cambio.valor), "fecha": cambio.fecha, "fuente": cambio.fuente}
    return Response(datos)


@api_view(["GET"])
def feriados(request):
    """GET /api/integraciones/feriados/?anio=2026 (sin año: el actual)"""
    anio = request.query_params.get("anio", "")
    anio = int(anio) if anio.isdecimal() and 2000 <= int(anio) <= 2100 else timezone.localdate().year

    try:
        lista = integraciones.feriados(anio, request.user)
    except integraciones.ApiNoDisponible as error:
        return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response([{"fecha": f.fecha, "nombre": f.nombre} for f in lista])



@api_view(["GET"])
def buscar_producto(request):
    """GET /api/integraciones/producto/?codigo_barras=0885909950805"""
    codigo_barras = request.query_params.get("codigo_barras", "").strip()
    if not codigo_barras.isdecimal() or not 8 <= len(codigo_barras) <= 14:
        return Response({"detail": "El código de barras debe tener entre 8 y 14 dígitos."}, status=400)

    try:
        datos = integraciones.buscar_producto(codigo_barras, request.user)
    except integraciones.ApiNoDisponible as error:
        return Response({"detail": str(error)}, status=503)
    if datos is None:
        return Response({"detail": "No se encontró información para ese código de barras."}, status=404)
    return Response(datos)
