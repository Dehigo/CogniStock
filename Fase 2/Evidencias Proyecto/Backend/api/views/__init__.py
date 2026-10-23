from api.views.auth import health_check, login, logout, usuario_actual
from api.views.inventario import (
    CategoriaViewSet,
    ProductoViewSet,
    ProveedorViewSet,
    producto_por_qr,
    registrar_salida,
)
from api.views.usuarios import RolViewSet, UsuarioViewSet
from api.views.bitacora import BitacoraViewSet
from api.views.parametros import ParametroViewSet
from api.views.cotizaciones import CotizacionViewSet, EntradaViewSet, EstadoCotizacionViewSet, MonedaViewSet
from api.views.movimientos import MovimientoViewSet
from api.views.agente import RecomendacionViewSet, consultar_agente
from api.views.integraciones import feriados, tipo_de_cambio
