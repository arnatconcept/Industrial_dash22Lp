from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Motor, Variador, Reparacion, OrdenMantenimiento, HistorialMantenimiento
from django.core.exceptions import ObjectDoesNotExist

@receiver(pre_save, sender=Motor)
@receiver(pre_save, sender=Variador)
def track_ubicacion_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_ubicacion_tipo = old_instance.ubicacion_tipo
        except ObjectDoesNotExist:
            instance._old_ubicacion_tipo = None

@receiver(post_save, sender=Motor)
@receiver(post_save, sender=Variador)
def crear_evento_ubicacion(sender, instance, created, **kwargs):
    tipo = 'motor' if sender == Motor else 'variador'
    
    if created:
        descripcion = f"Creación de {tipo} {instance.codigo}"
        tipo_evento = 'instalacion'
    else:
        if hasattr(instance, '_old_ubicacion_tipo') and instance._old_ubicacion_tipo != instance.ubicacion_tipo:
            descripcion = f"Cambio de ubicación: {instance.get_ubicacion_tipo_display()}"
            tipo_evento = 'movimiento'
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
def crear_evento_orden(sender, instance, created, **kwargs):
    if created:
        descripcion = f"Orden de mantenimiento creada: {instance.titulo}"
        tipo_evento = 'mantenimiento'
        
        for equipo in instance.equipos.all():
            HistorialMantenimiento.objects.create(
                equipo_tipo='motor',
                equipo_id=equipo.id,
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