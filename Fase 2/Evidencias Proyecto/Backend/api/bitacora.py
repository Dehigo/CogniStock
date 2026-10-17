from api.models import BitacoraAuditoria


def registrar_en_bitacora(request, accion, usuario=None, entidad="usuarios", entidad_id=None, detalle=None):
    BitacoraAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
        ip=request.META.get("REMOTE_ADDR"),
    )
