from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api import views

router = SimpleRouter()
router.register("usuarios", views.UsuarioViewSet, basename="usuario")
router.register("roles", views.RolViewSet, basename="rol")
router.register("categorias", views.CategoriaViewSet, basename="categoria")
router.register("productos", views.ProductoViewSet, basename="producto")
router.register("proveedores", views.ProveedorViewSet, basename="proveedor")
router.register("bitacora", views.BitacoraViewSet, basename="bitacora")
router.register("parametros", views.ParametroViewSet, basename="parametro")

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", views.logout, name="logout"),
    path("auth/me/", views.usuario_actual, name="usuario-actual"),
    path("productos/qr/", views.producto_por_qr, name="producto-por-qr"),
    path("salidas/", views.registrar_salida, name="registrar-salida"),
    path("", include(router.urls)),
]
