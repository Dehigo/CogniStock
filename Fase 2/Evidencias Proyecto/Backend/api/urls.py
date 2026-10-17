from django.urls import path

from api import views

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", views.logout, name="logout"),
    path("auth/me/", views.usuario_actual, name="usuario-actual"),
]
