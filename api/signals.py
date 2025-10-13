# signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from .models import Motor, Variador, Reparacion, OrdenMantenimiento, HistorialMantenimiento, ResultadoInspeccion
from .notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Motor)
@receiver(pre_save, sender=Variador)
def track_ubicacion_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_ubicacion_tipo = old_instance.ubicacion_tipo
            instance._old_estado = old_instance.estado
        except ObjectDoesNotExist:
            instance._old_ubicacion_tipo = None
            instance._old_estado = None

@receiver(post_save, sender=Motor)
@receiver(post_save, sender=Variador)
def crear_evento_ubicacion(sender, instance, created, **kwargs):
    tipo = 'motor' if sender == Motor else 'variador'
    
    if created:
        descripcion = f"Creación de {tipo} {instance.codigo}"
        tipo_evento = 'instalacion'
    else:
        # Verificar cambio de ubicación
        if hasattr(instance, '_old_ubicacion_tipo') and instance._old_ubicacion_tipo != instance.ubicacion_tipo:
            descripcion = f"Cambio de ubicación: {instance.get_ubicacion_tipo_display()}"
            tipo_evento = 'movimiento'
        # Verificar cambio de estado
        elif hasattr(instance, '_old_estado') and instance._old_estado != instance.estado:
            descripcion = f"Cambio de estado: {instance.get_estado_display()}"
            tipo_evento = 'mantenimiento'
        else:
            return
    
    HistorialMantenimiento.objects.create(
        equipo_tipo=tipo,
        equipo_id=instance.id,
        tipo_evento=tipo_evento,
        descripcion=descripcion,
        usuario=instance.creado_por
    )

@receiver(post_save, sender=Reparacion)
def crear_evento_reparacion(sender, instance, created, **kwargs):
    descripcion = f"Reparación {instance.get_tipo_display()} iniciada"
    tipo_evento = 'reparacion'
    
    HistorialMantenimiento.objects.create(
        equipo_tipo=instance.equipo_tipo,
        equipo_id=instance.equipo_id,
        tipo_evento=tipo_evento,
        descripcion=descripcion,
        usuario=instance.creado_por,
        reparacion=instance
    )

@receiver(post_save, sender=OrdenMantenimiento)
def manejar_notificaciones_orden(sender, instance, created, **kwargs):
    """Maneja notificaciones automáticas para órdenes de trabajo"""
    service = NotificationService()
    
    if created:
        # Nueva orden creada
        transaction.on_commit(
            lambda: service.notificar_nueva_orden(instance.id)
        )
    else:
        # Orden modificada - verificar cambio de estado
        if 'estado' in kwargs.get('update_fields', []):
            # Obtener usuario que hizo el cambio
            usuario_cambio_id = getattr(instance, '_current_user_id', None)
            if usuario_cambio_id:
                transaction.on_commit(
                    lambda: service.notificar_cambio_estado_orden(instance.id, usuario_cambio_id)
                )
    
    # Crear evento de historial
    if created:
        descripcion = f"Orden de mantenimiento creada: {instance.titulo}"
        tipo_evento = 'mantenimiento'
        
        for equipo in instance.equipos.all():
            HistorialMantenimiento.objects.create(
                equipo_tipo='equipo',
                equipo_id=equipo.id,
                tipo_evento=tipo_evento,
                descripcion=descripcion,
                usuario=instance.creado_por,
                orden=instance
            )
        
        for motor in instance.motores.all():
            HistorialMantenimiento.objects.create(
                equipo_tipo='motor',
                equipo_id=motor.id,
                tipo_evento=tipo_evento,
                descripcion=descripcion,
                usuario=instance.creado_por,
                orden=instance
            )
        
        for variador in instance.variadores.all():
            HistorialMantenimiento.objects.create(
                equipo_tipo='variador',
                equipo_id=variador.id,
                tipo_evento=tipo_evento,
                descripcion=descripcion,
                usuario=instance.creado_por,
                orden=instance
            )

@receiver(post_save, sender=ResultadoInspeccion)
def manejar_alerta_inspeccion(sender, instance, created, **kwargs):
    """Maneja alertas automáticas de inspecciones"""
    if created:
        service = NotificationService()
        desvio = abs(instance.valor_medido - instance.variable.valor_referencia)
        
        # Solo notificar si está fuera de tolerancia
        if desvio > instance.variable.tolerancia:
            transaction.on_commit(
                lambda: service.notificar_alerta_inspeccion(instance.id)
            )

# ✅ AGREGAR ESTA SEÑAL PARA INCIDENCIAS CRÍTICAS
@receiver(post_save, sender='api.IncidenciaReunion')  # Usar string reference para evitar importación circular
def manejar_incidencia_critica(sender, instance, created, **kwargs):
    """Maneja la creación automática de órdenes para incidencias críticas"""
    if created and instance.prioridad == "critica" and not instance.orden_mantenimiento:
        # Importar aquí para evitar circular imports
        from .models import OrdenMantenimiento
        from .tasks import crear_orden_desde_incidencia_critica
        
        # Ejecutar como tarea Celery para mejor performance
        crear_orden_desde_incidencia_critica.delay(instance.id)
        logger.info(f"📋 Tarea programada para crear orden desde incidencia crítica: {instance.id}")