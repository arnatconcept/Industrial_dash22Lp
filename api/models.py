from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db.models.functions import Abs


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('supervisor', 'Supervisor'),
        ('tecnico', 'Técnico'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tecnico')
    
    def save(self, *args, **kwargs):
        # Si es un nuevo usuario o se está cambiando la contraseña
        if not self.pk or 'password' in kwargs.get('update_fields', []):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class LineaProduccion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre

class Sector(models.Model):
    nombre = models.CharField(max_length=100)
    linea = models.ForeignKey(LineaProduccion, on_delete=models.CASCADE, related_name='sectores')
    
    class Meta:
        unique_together = [['nombre', 'linea']]
    
    def __str__(self):
        return f"{self.linea.nombre} - {self.nombre}"

class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='equipos')
    
    class Meta:
        unique_together = [['nombre', 'sector']]
    
    def __str__(self):
        return f"{self.sector} - {self.nombre}"

class Deposito(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return self.nombre

class UbicacionBase(models.Model):
    UBICACION_CHOICES = [
        ('linea', 'En línea de producción'),
        ('deposito', 'En depósito'),
        ('mantenimiento', 'En taller de mantenimiento'),
    ]
    
    ubicacion_tipo = models.CharField(
        max_length=20, 
        choices=UBICACION_CHOICES,
        default='linea'
    )
    linea = models.ForeignKey(
        LineaProduccion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    sector = models.ForeignKey(
        Sector, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    equipo = models.ForeignKey(
        Equipo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    deposito = models.ForeignKey(
        Deposito, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    class Meta:
        abstract = True

    def clean(self):
        # Validar consistencia de ubicación
        if self.ubicacion_tipo == 'linea':
            if not (self.linea and self.sector and self.equipo):
                raise ValidationError("Al estar en línea de producción, debe seleccionar línea, sector y equipo.")
            if self.deposito:
                raise ValidationError("No puede tener depósito asignado si está en línea de producción.")
        elif self.ubicacion_tipo == 'deposito':
            if not self.deposito:
                raise ValidationError("Debe seleccionar un depósito.")
            if self.linea or self.sector or self.equipo:
                raise ValidationError("No puede tener ubicación en producción si está en depósito.")
        elif self.ubicacion_tipo == 'mantenimiento':
            if self.linea or self.sector or self.equipo or self.deposito:
                raise ValidationError("En mantenimiento, no debe tener ubicación asignada.")

class EquipoBase(models.Model):
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'),
        ('reparacion', 'En Reparación'),
        ('baja', 'Dado de Baja'),
        ('standby', 'En Espera'),
    ]
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='operativo')
    fecha_instalacion = models.DateField(null=True, blank=True)
    ultimo_mantenimiento = models.DateField(null=True, blank=True)
    proximo_mantenimiento = models.DateField(null=True, blank=True)
    horas_uso = models.PositiveIntegerField(default=0)
    manual = models.FileField(upload_to='manuales/', null=True, blank=True)
    
    class Meta:
        abstract = True


class Motor(EquipoBase, UbicacionBase):
    codigo = models.CharField(max_length=100, unique=True)
    potencia = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)
    rpm = models.CharField(max_length=50)
    brida = models.CharField(max_length=50)
    anclaje = models.CharField(max_length=50)
    ref_plano = models.FileField(upload_to='plano_motores/', blank=True, null=True)
    imagen = models.ImageField(upload_to='motores/', blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='motores_creados')
    
    plano_url = models.CharField(max_length=500, blank=True, null=True)
    imagen_url = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        # Lógica de estado según ubicación
        if self.ubicacion_tipo == 'mantenimiento':
            self.estado = 'reparacion'
        elif self.ubicacion_tipo == 'deposito':
            self.estado = 'standby'
        elif self.ubicacion_tipo == 'linea' and self.estado == 'reparacion':
            self.estado = 'operativo'
        
        # Lógica de URLs de archivos
        if self.ref_plano and not self.plano_url:
            self.plano_url = self.ref_plano.url
        if self.imagen and not self.imagen_url:
            self.imagen_url = self.imagen.url
        
        # ✅ Lógica CORRECTA de próximo mantenimiento
        if self.estado == 'operativo':
            self._calcular_proximo_mantenimiento()
        else:
            self.proximo_mantenimiento = None
        
        # ✅ UN solo super().save() al final
        super().save(*args, **kwargs)

    def _calcular_proximo_mantenimiento(self):
        """Calcula próximo mantenimiento solo para equipos operativos"""
        from datetime import timedelta  # ✅ Importación local
        
        if self.ultimo_mantenimiento:
            # Basado en último mantenimiento + frecuencia (ej: 90 días)
            self.proximo_mantenimiento = self.ultimo_mantenimiento + timedelta(days=90)
        elif self.fecha_instalacion:
            # Equipo nuevo - primer mantenimiento (ej: 30 días)
            self.proximo_mantenimiento = self.fecha_instalacion + timedelta(days=30)
        else:
            self.proximo_mantenimiento = None
            
    def get_absolute_plano_url(self, request):
        if self.plano_url:
            return request.build_absolute_uri(self.plano_url)
        return None
        
    def get_absolute_imagen_url(self, request):
        if self.imagen_url:
            return request.build_absolute_uri(self.imagen_url)
        return None
    

class Variador(EquipoBase, UbicacionBase):
    codigo = models.CharField(max_length=100, unique=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    potencia = models.CharField(max_length=50)
    imagen = models.ImageField(upload_to='variadores/', blank=True, null=True)
    manual = models.FileField(upload_to='manuales_variadores/', blank=True, null=True)
    parametros = models.JSONField(default=dict, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='variadores_creados')

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        # Lógica de estado según ubicación
        if self.ubicacion_tipo == 'mantenimiento':
            self.estado = 'reparacion'
        elif self.ubicacion_tipo == 'deposito':
            self.estado = 'standby'
        elif self.ubicacion_tipo == 'linea' and self.estado == 'reparacion':
            self.estado = 'operativo'
        
        # ✅ Lógica CORRECTA de próximo mantenimiento
        if self.estado == 'operativo':
            self._calcular_proximo_mantenimiento()
        else:
            self.proximo_mantenimiento = None
        
        super().save(*args, **kwargs)

    def _calcular_proximo_mantenimiento(self):
        """Calcula próximo mantenimiento solo para equipos operativos"""
        from datetime import timedelta  # ✅ Importación local
        
        if self.ultimo_mantenimiento:
            self.proximo_mantenimiento = self.ultimo_mantenimiento + timedelta(days=90)
        elif self.fecha_instalacion:
            self.proximo_mantenimiento = self.fecha_instalacion + timedelta(days=30)
        else:
            self.proximo_mantenimiento = None

            
class OrdenMantenimiento(models.Model):
    TIPO_MANTENIMIENTO = [
        ('preventivo', 'Preventivo'),
        ('correctivo', 'Correctivo'),
        ('predictivo', 'Predictivo'),
        ('calibracion', 'Calibración'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('asignada', 'Asignada'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ]
    
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_MANTENIMIENTO, default='correctivo')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    operario_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_asignadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ordenes_creadas')
    tiempo_estimado = models.PositiveIntegerField(help_text="Tiempo estimado en minutos", null=True, blank=True)
    tiempo_real = models.PositiveIntegerField(help_text="Tiempo real en minutos", null=True, blank=True)
    checklist = models.JSONField(null=True, blank=True)  # Para listas de verificación dinámicas
    equipos = models.ManyToManyField('Equipo', blank=True)
    motores = models.ManyToManyField('Motor', blank=True)
    variadores = models.ManyToManyField('Variador', blank=True)

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.fecha_cierre and not self.operario_asignado:
            raise ValidationError("Debe asignar un operario antes de cerrar la orden")
        
        #if self.tipo == 'preventivo' and not self.proximo_mantenimiento:
        #    raise ValidationError("Las órdenes preventivas requieren fecha de próximo mantenimiento")

class Proveedor(models.Model):
    ESPECIALIDAD_CHOICES = [
        ('electrico', 'Eléctrico'),
        ('mecanico', 'Mecánico'),
        ('electronico', 'Electrónico'),
        ('hidraulico', 'Hidráulico'),
        ('neumatico', 'Neumático'),
        ('general', 'General'),
    ]
    
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=50, choices=ESPECIALIDAD_CHOICES)
    contacto = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_especialidad_display()})"

class Reparacion(models.Model):
    TIPO_REPARACION = [
        ('correctivo', 'Correctivo'),
        ('preventivo', 'Preventivo'),
        ('predictivo', 'Predictivo'),
        ('modificacion', 'Modificación'),
    ]
    
    equipo_tipo = models.CharField(max_length=20)  # 'motor' o 'variador'
    equipo_id = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_REPARACION)
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    documento = models.FileField(upload_to='reparaciones/', null=True, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Reparación {self.get_tipo_display()} - {self.fecha_inicio}"

class HistorialCambioOrden(models.Model):
    TIPO_CAMBIO_CHOICES = [
        ('descripcion', 'Descripción'),
        ('estado', 'Estado'),
        ('equipo', 'Equipo'),
        ('imagen', 'Imagen'),
    ]
    
    orden = models.ForeignKey(OrdenMantenimiento, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    tipo_cambio = models.CharField(max_length=20, choices=TIPO_CAMBIO_CHOICES)
    campo_afectado = models.CharField(max_length=50, null=True, blank=True)
    valor_anterior = models.TextField(null=True, blank=True)
    valor_nuevo = models.TextField(null=True, blank=True)
    equipo_tipo = models.CharField(max_length=20, null=True, blank=True)
    equipo_id = models.PositiveIntegerField(null=True, blank=True)
    imagen_url = models.URLField(null=True, blank=True)

class HistorialMantenimiento(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('instalacion', 'Instalación'),
        ('reparacion', 'Reparación'),
        ('mantenimiento', 'Mantenimiento'),
        ('baja', 'Baja'),
        ('movimiento', 'Movimiento de ubicación'),
    ]
    
    equipo_tipo = models.CharField(max_length=20)
    equipo_id = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES)
    descripcion = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    orden = models.ForeignKey(OrdenMantenimiento, on_delete=models.SET_NULL, null=True, blank=True)
    reparacion = models.ForeignKey(Reparacion, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tipo_evento_display()} - {self.fecha}"

class Evento(models.Model):
    TIPO_CHOICES = [
        ('motor', 'Motor'),
        ('variador', 'Variador'),
        ('orden', 'Orden de Mantenimiento'),
        ('reparacion', 'Reparación'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    objeto_id = models.IntegerField()

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha}"
    

class PLC(models.Model):
    TIPO_CHOICES = [
        ('siemens', 'Siemens'),
        ('allen_bradley', 'Allen-Bradley'),
        ('schneider', 'Schneider'),
        ('delta', 'Delta'),
        ('omron', 'Omron'),
        ('otros', 'Otros'),
    ]
    
    nombre = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    direccion_ip = models.GenericIPAddressField(blank=True, null=True)
    ubicacion = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)
    firmware = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    diagrama = models.FileField(upload_to='diagramas_plc/', blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_instalacion = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.tipo.upper()} {self.modelo} - {self.nombre}"

class PLCEntradaSalida(models.Model):
    TIPO_IO = [
        ('digital_in', 'Entrada Digital'),
        ('digital_out', 'Salida Digital'),
        ('analog_in', 'Entrada Analógica'),
        ('analog_out', 'Salida Analógica'),
        ('especial', 'Función Especial'),
    ]
    
    plc = models.ForeignKey(PLC, on_delete=models.CASCADE, related_name='entradas_salidas')
    direccion = models.CharField(max_length=50)  # Ej: I0.1, Q0.5, AI1, etc.
    tipo = models.CharField(max_length=50, choices=TIPO_IO)
    etiqueta = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    valor_actual = models.CharField(max_length=50, blank=True)
    rango = models.CharField(max_length=100, blank=True)  # Ej: 0-10V, 4-20mA
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    historico = models.JSONField(default=list, blank=True)  # Registro histórico
    
    class Meta:
        unique_together = [['plc', 'direccion']]
        ordering = ['tipo', 'direccion']
        verbose_name = 'Entrada/Salida PLC'
        verbose_name_plural = 'Entradas/Salidas PLC'

    def __str__(self):
        return f"{self.plc.nombre} - {self.direccion} ({self.etiqueta})"

class PLCLog(models.Model):
    TIPO_LOG = [
        ('configuracion', 'Cambio de Configuración'),
        ('valor', 'Cambio de Valor'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    
    plc = models.ForeignKey(PLC, on_delete=models.CASCADE)
    entrada_salida = models.ForeignKey(PLCEntradaSalida, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=TIPO_LOG)
    valor_anterior = models.CharField(max_length=100, blank=True)
    valor_nuevo = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['plc', 'fecha']),
        ]

    def __str__(self):
        return f"{self.plc} - {self.get_tipo_display()} @ {self.fecha}"
    


class RutaInspeccion(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    activo_tipo = models.CharField(max_length=50)  # 'motor', 'variador', 'equipo'
    activo_id = models.IntegerField()
    frecuencia_dias = models.PositiveIntegerField(help_text="Cada cuántos días debe repetirse")
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} [{self.activo_tipo} #{self.activo_id}]"

class VariableInspeccion(models.Model):
    ruta = models.ForeignKey(RutaInspeccion, on_delete=models.CASCADE, related_name='variables')
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=50)
    valor_referencia = models.FloatField()
    tolerancia = models.FloatField(help_text="Rango permitido (+/-)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ruta.nombre} → {self.nombre}"

class InspeccionEjecucion(models.Model):
    ruta = models.ForeignKey(RutaInspeccion, on_delete=models.CASCADE, related_name='ejecuciones')
    tecnico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ruta.nombre} ejecutada por {self.tecnico} en {self.fecha.strftime('%Y-%m-%d %H:%M')}"

class ResultadoInspeccion(models.Model):
    ejecucion = models.ForeignKey(InspeccionEjecucion, on_delete=models.CASCADE, related_name='resultados')
    variable = models.ForeignKey(VariableInspeccion, on_delete=models.CASCADE)
    valor_medido = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Lógica automática de verificación y alerta
        desvio = abs(self.valor_medido - self.variable.valor_referencia)
        if desvio > self.variable.tolerancia:
            severidad = 'moderado'
            if desvio > self.variable.tolerancia * 2:
                severidad = 'crítico'
            elif desvio < self.variable.tolerancia * 1.2:
                severidad = 'leve'

            Evento.objects.create(
                tipo=self.ejecucion.ruta.activo_tipo,
                descripcion=f"Alerta [{severidad}]: {self.variable.nombre} fuera de rango. "
                            f"Medido: {self.valor_medido} (Ref: {self.variable.valor_referencia} ±{self.variable.tolerancia})",
                usuario=self.ejecucion.tecnico,
                objeto_id=self.ejecucion.ruta.activo_id
            )
        ultimos = ResultadoInspeccion.objects.filter(
            variable=self.variable
        ).order_by('-fecha')[:5]

        if ultimos.count() >= 3:
            valores = [r.valor_medido for r in ultimos]
            promedio = sum(valores) / len(valores)
            if abs(promedio - self.variable.valor_referencia) > self.variable.tolerancia:
                Evento.objects.create(
                    tipo=self.ejecucion.ruta.activo_tipo,
                    descripcion=f"Predicción: tendencia anómala detectada en {self.variable.nombre}. "
                                f"Promedio móvil: {promedio:.2f}",
                    usuario=self.ejecucion.tecnico,
                    objeto_id=self.ejecucion.ruta.activo_id
                )

    
class NotificacionApp(models.Model):
    TIPO_NOTIFICACION_CHOICES = [
        ('revision', 'Próxima Revisión'),
        ('inspeccion', 'Inspección Pendiente'),
        ('mantenimiento', 'Mantenimiento Programado'),
        ('alerta', 'Alerta de Equipo'),
        ('parada', 'Parada de Producción'),
        ('falla', 'Falla Detectada'),
        ('completado', 'Tarea Completada'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    # Destinatario
    usuario_id = models.IntegerField()  # ID del usuario, no ForeignKey para independencia
    usuario_nombre = models.CharField(max_length=150)
    
    # Contenido
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICACION_CHOICES)
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES)
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    leida = models.BooleanField(default=False)
    
    # Datos adicionales para la app
    data_adicional = models.JSONField(default=dict, blank=True)
    relacion_id = models.IntegerField(null=True, blank=True)  # ID de orden, activo, etc.
    relacion_tipo = models.CharField(max_length=50, blank=True)  # 'orden', 'activo', 'parada'
    
    # Control FCM
    enviada_push = models.BooleanField(default=False)
    intentos_envio = models.IntegerField(default=0)
    error_envio = models.TextField(blank=True)
    
    class Meta:
        db_table = 'app_notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario_id', 'leida']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.tipo} - {self.usuario_nombre}"


class DispositivoApp(models.Model):
    """Registro de dispositivos móviles para FCM"""
    usuario_id = models.IntegerField()  # ID del usuario en el sistema existente
    usuario_nombre = models.CharField(max_length=150)
    token_fcm = models.CharField(max_length=255, unique=True)
    plataforma = models.CharField(max_length=20)  # 'android', 'ios'
    version_app = models.CharField(max_length=20, blank=True)
    esta_activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'app_dispositivos'
    
    def __str__(self):
        return f"{self.usuario_nombre} - {self.plataforma}"