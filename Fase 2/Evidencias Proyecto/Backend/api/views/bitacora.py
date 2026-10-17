from rest_framework import viewsets
from rest_framework.response import Response

from api.models import BitacoraAuditoria
from api.permissions import EsAdministrador
from api.serializers import BitacoraSerializer

LIMITE_REGISTROS = 200


class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BitacoraSerializer
    permission_classes = [EsAdministrador]

    def get_queryset(self):
        registros = BitacoraAuditoria.objects.select_related("usuario").order_by("-fecha")

        entidad = self.request.query_params.get("entidad")
        if entidad:
            registros = registros.filter(entidad=entidad)

        return registros

    def list(self, request, *args, **kwargs):
        registros = self.get_queryset()[:LIMITE_REGISTROS]
        return Response(self.get_serializer(registros, many=True).data)
