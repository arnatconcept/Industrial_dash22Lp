# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import NotificacionApp, Motor, Variador, OrdenMantenimiento
from .notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

@shared_task
def verificar_mantenimientos_preventivos():
    """Verifica y notifica mantenimientos preventivos próximos"""
    service = NotificationService()
    hoy = timezone.now().date()
    
    # Verificar 
    motores = Motor.objects.filter(proximo_mantenimiento__isnull=False, estado='operativo')
    for motor in motores:
        dias_restantes = (motor.proximo_mantenimiento - hoy).days
        if 0 <= dias_restantes <= 7:  # Notificar si queda una semana o menos
            service.notificar_mantenimiento_preventivo('motor', motor.pk, dias_restantes)
    
    # Verificar variadores
    variadores = Variador.objects.filter(proximo_mantenimiento__isnull=False, estado='operativo')
    for variador in variadores:
        dias_restantes = (variador.proximo_mantenimiento - hoy).days
        if 0 <= dias_restantes <= 7:
            service.notificar_mantenimiento_preventivo('variador', variador.pk, dias_restantes)

@shared_task
def recordatorios_ordenes_pendientes():
    """Envía recordatorios de órdenes pendientes"""
    service = NotificationService()
    
    # Órdenes pendientes por más de 24 horas
    limite_tiempo = timezone.now() - timedelta(hours=24)
    ordenes_pendientes = OrdenMantenimiento.objects.filter(
        estado='pendiente',
        fecha_creacion__lte=limite_tiempo
    )
    
    for orden in ordenes_pendientes:
        titulo = "⏰ Orden Pendiente"
        mensaje = f"La orden #{orden.id} lleva más de 24 horas pendiente"
        
        # Notificar al creador de la orden
        if orden.creado_por:
            service.enviar_notificacion_individual(
                usuario_id=orden.creado_por.id,
                titulo=titulo,
                mensaje=mensaje,
                tipo="recordatorio_orden",
                prioridad="media",
                relacion_id=orden.id,
                relacion_tipo="orden"
            )

@shared_task
def reintentar_notificaciones_fallidas():
    """Reintenta enviar notificaciones que fallaron anteriormente"""
    service = NotificationService()
    notificaciones_fallidas = NotificacionApp.objects.filter(
        enviada_push=False,
        intentos_envio__lt=3,  # Máximo 3 intentos
        fecha_creacion__gte=timezone.now() - timedelta(hours=24)
    )
    
    for notificacion in notificaciones_fallidas:
        service.enviar_notificacion_individual(
            usuario_id=notificacion.usuario_id,
            titulo=notificacion.titulo,
            mensaje=notificacion.mensaje,
            tipo=notificacion.tipo,
            prioridad=notificacion.prioridad,
            data_adicional=notificacion.data_adicional,
            relacion_id=notificacion.relacion_id,
            relacion_tipo=notificacion.relacion_tipo
        )