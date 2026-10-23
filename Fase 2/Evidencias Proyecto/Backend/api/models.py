import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


# Seguridad y administración

class Rol(models.Model):
    ADMINISTRADOR = "Administrador"
    ENCARGADO = "Encargado de inventario"
    OPERATIVO = "Usuario operativo"

    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    permisos = models.ManyToManyField("Permiso", through="RolPermiso", related_name="roles")

    class Meta:
        db_table = "roles"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email.")
        if "rol" not in extra_fields and "rol_id" not in extra_fields:
            raise ValueError("El usuario debe tener un rol.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        if "rol" not in extra_fields and "rol_id" not in extra_fields:
            extra_fields["rol"], _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        return self._create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    username = None
    first_name = None
    last_name = None

    nombre = models.CharField(max_length=120)
    email = models.EmailField(max_length=150, unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name="usuarios")
    is_active = models.BooleanField(default=True, db_column="activo")
    date_joined = models.DateTimeField(default=timezone.now, db_column="creado_en")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    objects = UsuarioManager()

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return f"{self.nombre} <{self.email}>"


class Permiso(models.Model):
    codigo = models.CharField(max_length=60, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "permisos"

    def __str__(self):
        return self.codigo


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    class Meta:
        db_table = "rol_permisos"
        constraints = [
            models.UniqueConstraint(fields=["rol", "permiso"], name="uq_rol_permiso"),
        ]


class ParametroSistema(models.Model):
    clave = models.CharField(max_length=80, unique=True)
    valor = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255, blank=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parametros_actualizados",
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parametros_sistema"

    def __str__(self):
        return self.clave


class BitacoraAuditoria(models.Model):
    # Puede quedar sin usuario, por ejemplo en un intento de login fallido.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="acciones_auditadas",
    )
    accion = models.CharField(max_length=50)
    entidad = models.CharField(max_length=50)
    entidad_id = models.BigIntegerField(null=True, blank=True)
    detalle = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bitacora_auditoria"
        indexes = [
            models.Index(fields=["entidad", "entidad_id"], name="idx_bitacora_entidad"),
            models.Index(fields=["-fecha"], name="idx_bitacora_fecha"),
        ]


# Productos y proveedores

class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "categorias_producto"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=80, unique=True)
    codigo_qr = models.CharField(max_length=255, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="productos",
    )
    unidad_medida = models.CharField(max_length=30, default="unidad")
    precio_referencia = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "productos"
        constraints = [
            models.CheckConstraint(condition=Q(precio_referencia__gte=0), name="ck_producto_precio_ref"),
            models.CheckConstraint(condition=Q(stock_minimo__gte=0), name="ck_producto_stock_minimo"),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def save(self, *args, **kwargs):
        # Si el producto no trae código de barras propio, se le asigna uno interno para imprimir su etiqueta.
        if not self.codigo_qr:
            self.codigo_qr = f"CS-{secrets.token_hex(4).upper()}"
        super().save(*args, **kwargs)


class DatoProductoExterno(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="datos_externos")
    fuente = models.CharField(max_length=50)
    codigo_barras = models.CharField(max_length=80, blank=True)
    marca = models.CharField(max_length=150, blank=True)
    descripcion_externa = models.TextField(blank=True)
    imagen_url = models.URLField(max_length=500, blank=True)
    datos = models.JSONField(null=True, blank=True)
    consultado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "datos_producto_externo"
        constraints = [
            models.UniqueConstraint(fields=["producto", "fuente"], name="uq_dato_externo_producto_fuente"),
        ]


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    rut = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=150, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "proveedores"
        verbose_name_plural = "proveedores"

    def __str__(self):
        return self.nombre


class ProveedorProducto(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="productos_ofrecidos")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="proveedores")
    codigo_proveedor = models.CharField(max_length=80, blank=True)
    ultimo_precio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "proveedor_producto"
        constraints = [
            models.UniqueConstraint(fields=["proveedor", "producto"], name="uq_proveedor_producto"),
            models.CheckConstraint(condition=Q(ultimo_precio__gte=0), name="ck_proveedor_producto_precio"),
        ]


# Cotizaciones

class Moneda(models.Model):
    codigo = models.CharField(max_length=3, unique=True)
    nombre = models.CharField(max_length=50)
    simbolo = models.CharField(max_length=5, blank=True)

    class Meta:
        db_table = "monedas"

    def __str__(self):
        return self.codigo


class EstadoCotizacion(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    permite_entrada = models.BooleanField(default=False)

    class Meta:
        db_table = "estados_cotizacion"
        verbose_name_plural = "estados de cotización"

    def __str__(self):
        return self.codigo


class Cotizacion(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="cotizaciones")
    numero = models.CharField(max_length=60, unique=True)
    moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, related_name="cotizaciones")
    estado = models.ForeignKey(EstadoCotizacion, on_delete=models.PROTECT, related_name="cotizaciones")
    fecha = models.DateField(default=timezone.localdate)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cotizaciones_creadas",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cotizaciones"
        verbose_name_plural = "cotizaciones"
        indexes = [models.Index(fields=["proveedor"], name="idx_cotizaciones_proveedor")]

    def __str__(self):
        return self.numero


class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_cotizacion")
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "detalle_cotizacion"
        constraints = [
            models.UniqueConstraint(fields=["cotizacion", "producto"], name="uq_detalle_cotizacion_producto"),
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="ck_detalle_cotizacion_cantidad"),
            models.CheckConstraint(condition=Q(precio_unitario__gte=0), name="ck_detalle_cotizacion_precio"),
        ]
        indexes = [models.Index(fields=["producto"], name="idx_detalle_cotizacion_prod")]


class HistorialEstadoCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="historial_estados")
    estado_anterior = models.ForeignKey(
        EstadoCotizacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    estado_nuevo = models.ForeignKey(EstadoCotizacion, on_delete=models.PROTECT, related_name="+")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    motivo = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_estado_cotizacion"


# Inventario: stock, entradas y salidas

class Stock(models.Model):
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="stock",
    )
    cantidad = models.IntegerField(default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock"
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gte=0), name="ck_stock_no_negativo"),
        ]


class Entrada(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.PROTECT, related_name="entradas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entradas")
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "entradas"


class DetalleEntrada(models.Model):
    entrada = models.ForeignKey(Entrada, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_entrada")
    cantidad = models.IntegerField()

    class Meta:
        db_table = "detalle_entrada"
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="ck_detalle_entrada_cantidad"),
        ]


class Salida(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="salidas")
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "salidas"


class DetalleSalida(models.Model):
    salida = models.ForeignKey(Salida, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_salida")
    cantidad = models.IntegerField()
    codigo_qr = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "detalle_salida"
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="ck_detalle_salida_cantidad"),
        ]


class Movimiento(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="movimientos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    cantidad = models.IntegerField()
    entrada = models.ForeignKey(
        Entrada,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos",
    )
    salida = models.ForeignKey(
        Salida,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = "movimientos"
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=["ENTRADA", "SALIDA"]), name="ck_movimiento_tipo"),
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="ck_movimiento_cantidad"),
            # Una entrada apunta solo a su entrada y una salida solo a su salida.
            models.CheckConstraint(
                condition=(
                    Q(tipo="ENTRADA", entrada__isnull=False, salida__isnull=True)
                    | Q(tipo="SALIDA", salida__isnull=False, entrada__isnull=True)
                ),
                name="ck_movimiento_referencia",
            ),
        ]
        indexes = [models.Index(fields=["producto", "-fecha"], name="idx_movimientos_producto_fecha")]


class EscaneoQR(models.Model):
    class Resultado(models.TextChoices):
        OK = "OK", "Salida registrada"
        SIN_STOCK = "SIN_STOCK", "Stock insuficiente"
        QR_INVALIDO = "QR_INVALIDO", "QR no reconocido"

    codigo_leido = models.CharField(max_length=255)
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="escaneos",
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="escaneos_qr")
    resultado = models.CharField(max_length=20, choices=Resultado.choices)
    salida = models.ForeignKey(
        Salida,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="escaneos",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "escaneos_qr"
        constraints = [
            models.CheckConstraint(
                condition=Q(resultado__in=["OK", "SIN_STOCK", "QR_INVALIDO"]),
                name="ck_escaneo_resultado",
            ),
        ]


class AlertaStock(models.Model):
    class Tipo(models.TextChoices):
        STOCK_BAJO = "STOCK_BAJO", "Stock bajo el mínimo"
        SIN_STOCK = "SIN_STOCK", "Sin stock"

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        ATENDIDA = "ATENDIDA", "Atendida"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="alertas")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    cantidad_al_generar = models.IntegerField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    atendida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    atendida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "alertas_stock"
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=["STOCK_BAJO", "SIN_STOCK"]), name="ck_alerta_tipo"),
            models.CheckConstraint(condition=Q(estado__in=["ACTIVA", "ATENDIDA"]), name="ck_alerta_estado"),
            # Evita alertas repetidas: solo puede haber una activa por producto y tipo.
            models.UniqueConstraint(
                fields=["producto", "tipo"],
                condition=Q(estado="ACTIVA"),
                name="uq_alerta_activa_producto_tipo",
            ),
        ]


# Integraciones externas

class TipoCambio(models.Model):
    moneda_origen = models.ForeignKey(Moneda, on_delete=models.PROTECT, related_name="+")
    moneda_destino = models.ForeignKey(Moneda, on_delete=models.PROTECT, related_name="+")
    valor = models.DecimalField(max_digits=18, decimal_places=6)
    fecha = models.DateField()
    fuente = models.CharField(max_length=50, default="Frankfurter")
    consultado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tipos_cambio"
        constraints = [
            models.UniqueConstraint(
                fields=["moneda_origen", "moneda_destino", "fecha"],
                name="uq_tipo_cambio_dia",
            ),
            models.CheckConstraint(condition=Q(valor__gt=0), name="ck_tipo_cambio_valor"),
            models.CheckConstraint(
                condition=~Q(moneda_origen=F("moneda_destino")),
                name="ck_tipo_cambio_monedas_distintas",
            ),
        ]


class Feriado(models.Model):
    fecha = models.DateField()
    nombre = models.CharField(max_length=150)
    pais = models.CharField(max_length=2, default="CL")

    class Meta:
        db_table = "feriados"
        constraints = [
            models.UniqueConstraint(fields=["fecha", "pais"], name="uq_feriado_fecha_pais"),
        ]


class LlamadaApiExterna(models.Model):
    class Servicio(models.TextChoices):
        FRANKFURTER = "FRANKFURTER", "Frankfurter"
        NAGER_DATE = "NAGER_DATE", "Nager.Date"
        PRODUCTOS = "PRODUCTOS", "API de productos"
        GROQ = "GROQ", "Groq API"

    servicio = models.CharField(max_length=20, choices=Servicio.choices)
    endpoint = models.CharField(max_length=500)
    metodo = models.CharField(max_length=10, default="GET")
    estado_http = models.PositiveSmallIntegerField(null=True, blank=True)
    exito = models.BooleanField()
    mensaje_error = models.TextField(blank=True)
    duracion_ms = models.PositiveIntegerField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llamadas_api_externa"
        constraints = [
            models.CheckConstraint(
                condition=Q(servicio__in=["FRANKFURTER", "NAGER_DATE", "PRODUCTOS", "GROQ"]),
                name="ck_llamada_api_servicio",
            ),
        ]
        indexes = [models.Index(fields=["servicio", "-fecha"], name="idx_llamadas_api_servicio")]


# Agente de IA

class ConversacionAgente(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conversaciones_agente",
    )
    pregunta = models.TextField()
    respuesta = models.TextField(blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    tokens_usados = models.PositiveIntegerField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversaciones_agente"


class EjecucionToolAgente(models.Model):
    conversacion = models.ForeignKey(
        ConversacionAgente,
        on_delete=models.CASCADE,
        related_name="ejecuciones_tool",
    )
    tool = models.CharField(max_length=80)
    parametros = models.JSONField(default=dict, blank=True)
    resultado = models.JSONField(null=True, blank=True)
    permitido = models.BooleanField()
    motivo_rechazo = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ejecuciones_tool_agente"


class RecomendacionReposicion(models.Model):
    class Estado(models.TextChoices):
        PROPUESTA = "PROPUESTA", "Propuesta"
        ACEPTADA = "ACEPTADA", "Aceptada"
        DESCARTADA = "DESCARTADA", "Descartada"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="recomendaciones")
    proveedor_sugerido = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recomendaciones",
    )
    cantidad_sugerida = models.IntegerField()
    justificacion = models.TextField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROPUESTA)
    conversacion = models.ForeignKey(
        ConversacionAgente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recomendaciones",
    )
    revisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    revisada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "recomendaciones_reposicion"
        constraints = [
            models.CheckConstraint(condition=Q(cantidad_sugerida__gt=0), name="ck_recomendacion_cantidad"),
            models.CheckConstraint(
                condition=Q(estado__in=["PROPUESTA", "ACEPTADA", "DESCARTADA"]),
                name="ck_recomendacion_estado",
            ),
        ]
