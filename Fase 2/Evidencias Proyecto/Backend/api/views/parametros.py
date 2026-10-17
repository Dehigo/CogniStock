from rest_framework import viewsets

from api.bitacora import registrar_en_bitacora
from api.models import ParametroSistema
from api.permissions import EsAdministrador
from api.serializers import ParametroSerializer


class ParametroViewSet(viewsets.ModelViewSet):
    queryset = ParametroSistema.objects.select_related("actualizado_por").order_by("clave")
    serializer_class = ParametroSerializer
    permission_classes = [EsAdministrador]
    http_method_names = ["get", "post", "patch", "delete"]

    def perform_create(self, serializer):
        parametro = serializer.save(actualizado_por=self.request.user)
        registrar_en_bitacora(self.request, "PARAMETRO_CREADO", self.request.user, "parametros", parametro.id)

    def perform_update(self, serializer):
        parametro = serializer.save(actualizado_por=self.request.user)
        registrar_en_bitacora(self.request, "PARAMETRO_EDITADO", self.request.user, "parametros", parametro.id)

    def perform_destroy(self, parametro):
        registrar_en_bitacora(
            self.request, "PARAMETRO_ELIMINADO", self.request.user, "parametros", parametro.id,
            detalle={"clave": parametro.clave},
        )
        parametro.delete()
