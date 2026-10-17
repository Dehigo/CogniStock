from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api import views

router = SimpleRouter()
router.register("usuarios", views.UsuarioViewSet, basename="usuario")
router.register("roles", views.RolViewSet, basename="rol")

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", views.logout, name="logout"),
    path("auth/me/", views.usuario_actual, name="usuario-actual"),
    path("", include(router.urls)),
]
