# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import NotificacionApp, Motor, Variador, OrdenMantenimiento
from .notification_service import NotificationService
import logging
import requests
from django.core.cache import cache
from django.db import connection
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)

# ==================== TAREAS PRINCIPALES ====================

@shared_task
def verificar_mantenimientos_preventivos():
    """Verifica y notifica mantenimientos preventivos próximos"""
    try:
        service = NotificationService()
        hoy = timezone.now().date()
        
        # Verificar motores
        motores = Motor.objects.filter(proximo_mantenimiento__isnull=False, estado='operativo')
        for motor in motores:
            dias_restantes = (motor.proximo_mantenimiento - hoy).days
            if 0 <= dias_restantes <= 7:
                service.notificar_mantenimiento_preventivo('motor', motor.pk, dias_restantes)
        
        # Verificar variadores
        variadores = Variador.objects.filter(proximo_mantenimiento__isnull=False, estado='operativo')
        for variador in variadores:
            dias_restantes = (variador.proximo_mantenimiento - hoy).days
            if 0 <= dias_restantes <= 7:
                service.notificar_mantenimiento_preventivo('variador', variador.pk, dias_restantes)
        
        logger.info(f"✅ Mantenimientos preventivos verificados: {len(motores)} motores, {len(variadores)} variadores")
        return f"Procesados {len(motores)} motores y {len(variadores)} variadores"
    
    except Exception as e:
        logger.error(f"❌ Error en verificar_mantenimientos_preventivos: {e}")
        raise

@shared_task
def recordatorios_ordenes_pendientes():
    """Envía recordatorios de órdenes pendientes"""
    try:
        service = NotificationService()
        limite_tiempo = timezone.now() - timedelta(hours=24)
        ordenes_pendientes = OrdenMantenimiento.objects.filter(
            estado='pendiente',
            fecha_creacion__lte=limite_tiempo
        )
        
        for orden in ordenes_pendientes:
            if orden.creado_por:
                service.enviar_notificacion_individual(
                    usuario_id=orden.creado_por.id,
                    titulo="⏰ Orden Pendiente",
                    mensaje=f"La orden #{orden.id} lleva más de 24 horas pendiente",
                    tipo="recordatorio_orden",
                    prioridad="media",
                    relacion_id=orden.id,
                    relacion_tipo="orden"
                )
        
        logger.info(f"✅ Recordatorios enviados para {len(ordenes_pendientes)} órdenes")
        return f"Procesadas {len(ordenes_pendientes)} órdenes pendientes"
    
    except Exception as e:
        logger.error(f"❌ Error en recordatorios_ordenes_pendientes: {e}")
        raise

#@shared_task
#def reintentar_notificaciones_fallidas():
#    """Reintenta enviar notificaciones que fallaron anteriormente"""
#    try:
#        service = NotificationService()
#        notificaciones_fallidas = NotificacionApp.objects.filter(
#            enviada_push=False,
#            intentos_envio__lt=3,
#            fecha_creacion__gte=timezone.now() - timedelta(hours=24)
#        )
#        for notificacion in notificaciones_fallidas:
 #           service.enviar_notificacion_individual(
  #              usuario_id=notificacion.usuario_id,
   #             titulo=notificacion.titulo,
    #            mensaje=notificacion.mensaje,
     #           tipo=notificacion.tipo,
      #          prioridad=notificacion.prioridad,
       #         data_adicional=notificacion.data_adicional,
        #        relacion_id=notificacion.relacion_id,
         #       relacion_tipo=notificacion.relacion_tipo
          #  )
        #
#        logger.info(f"✅ Reintentadas {len(notificaciones_fallidas)} notificaciones")
 #       return f"Reintentadas {len(notificaciones_fallidas)} notificaciones"
    
  #  except Exception as e:
   #     logger.error(f"❌ Error en reintentar_notificaciones_fallidas: {e}")
    #    raise

@shared_task
def limpiar_dispositivos_inactivos():
    """Limpia dispositivos marcados como inactivos por mucho tiempo"""
    try:
        from .models import Dispositivo
        limite_tiempo = timezone.now() - timedelta(days=30)
        
        dispositivos_inactivos = Dispositivo.objects.filter(
            estado='inactivo',
            updated_at__lte=limite_tiempo
        )
        
        count = dispositivos_inactivos.count()
        dispositivos_inactivos.delete()
        
        logger.info(f"✅ Limpiados {count} dispositivos inactivos")
        return f"Eliminados {count} dispositivos inactivos"
    
    except Exception as e:
        logger.error(f"❌ Error en limpiar_dispositivos_inactivos: {e}")
        raise

@shared_task
def crear_reunion_diaria():
    """Crea la reunión diaria automáticamente"""
    try:
        from .models import ReunionDiaria, User
        
        hoy = timezone.now().date()
        reunion, creada = ReunionDiaria.objects.get_or_create(fecha=hoy)
        
        if creada:
            service = NotificationService()
            supervisores = User.objects.filter(role__in=["supervisor", "admin"], is_active=True)
            
            for sup in supervisores:
                service.enviar_notificacion_individual(
                    usuario_id=sup.id,
                    titulo="📅 Reunión programada",
                    mensaje=f"Se creó la reunión del día {hoy}",
                    tipo="reunion_diaria",
                    prioridad="media",
                    relacion_id=reunion.id,
                    relacion_tipo="reunion"
                )
        
        logger.info(f"✅ Reunión diaria {'creada' if creada else 'existente'}")
        return f"Reunión {reunion.fecha} {'creada' if creada else 'ya existía'}"
    
    except Exception as e:
        logger.error(f"❌ Error en crear_reunion_diaria: {e}")
        raise

@shared_task
def cerrar_reuniones_no_realizadas():
    """Cierra reuniones que no se realizaron a tiempo"""
    try:
        from .models import ReunionDiaria, User
        
        ahora = timezone.now()
        limite = ahora - timedelta(hours=12)
        pendientes = ReunionDiaria.objects.filter(
            fecha__lt=ahora.date(), 
            estado="programada"
        )
        
        service = NotificationService()
        for reunion in pendientes:
            reunion.estado = "anulada"
            reunion.motivo_anulacion = "No se realizó la reunión a tiempo"
            reunion.save()

            supervisores = User.objects.filter(role="supervisor", is_active=True)
            for sup in supervisores:
                service.enviar_notificacion_individual(
                    usuario_id=sup.id,
                    titulo="⚠️ Reunión anulada",
                    mensaje=f"La reunión del {reunion.fecha} fue anulada automáticamente",
                    tipo="reunion_diaria",
                    prioridad="alta",
                    relacion_id=reunion.id,
                    relacion_tipo="reunion"
                )
        
        logger.info(f"✅ Cerradas {len(pendientes)} reuniones no realizadas")
        return f"Anuladas {len(pendientes)} reuniones"
    
    except Exception as e:
        logger.error(f"❌ Error en cerrar_reuniones_no_realizadas: {e}")
        raise

@shared_task
def crear_orden_desde_incidencia_critica(incidencia_id):
    """
    Tarea Celery para crear orden de mantenimiento desde incidencia crítica
    """
    try:
        from .models import IncidenciaReunion, OrdenMantenimiento
        
        incidencia = IncidenciaReunion.objects.get(id=incidencia_id)
        
        orden = OrdenMantenimiento.objects.create(
            titulo=f"Reparación crítica - {incidencia.equipo_relacionado or 'Equipo'}",
            descripcion=incidencia.descripcion,
            tipo="correctivo",
            prioridad="critica",
            creado_por=incidencia.reportada_por
        )
        
        incidencia.orden_mantenimiento = orden
        incidencia.save()

        NotificationService().notificar_nueva_orden(orden.id)
        logger.info(f"✅ Orden creada desde incidencia crítica: {orden.id}")
        
        return f"Orden {orden.id} creada exitosamente"
    
    except Exception as e:
        logger.error(f"❌ Error creando orden desde incidencia {incidencia_id}: {e}")
        raise

# ==================== TAREAS DE PRUEBA ====================

@shared_task(bind=True, max_retries=3)
def tarea_prueba_celery(self, mensaje_personalizado=None):
    """Tarea de prueba para verificar que Celery está funcionando correctamente"""
    try:
        inicio = timezone.now()
        
        test_data = {
            'timestamp_inicio': inicio.isoformat(),
            'mensaje': mensaje_personalizado or 'Tarea de prueba ejecutada',
            'worker': 'celery@' + str(self.request.hostname),
            'intento': self.request.retries
        }
        
        # Prueba simple de funcionamiento
        import time
        time.sleep(1)  # Simular trabajo
        
        fin = timezone.now()
        duracion = (fin - inicio).total_seconds()
        
        resultado = {
            'estado': 'completado',
            'duracion_segundos': duracion,
            'timestamp_fin': fin.isoformat(),
            'tarea_id': self.request.id,
            'test_data': test_data
        }
        
        logger.info(f"✅ Tarea de prueba completada: {resultado}")
        return resultado
    
    except Exception as e:
        logger.error(f"❌ Error en tarea de prueba: {str(e)}")
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            raise self.retry(exc=e, countdown=countdown)
        
        return {'estado': 'error', 'error': str(e), 'intentos': self.request.retries + 1}

@shared_task
def prueba_servicios_externos():
    """Prueba la conectividad con servicios externos"""
    servicios = {}
    
    # Prueba de FCM
    try:
        service = NotificationService()
        fcm_key_exists = bool(service.fcm_server_key)
        servicios['fcm'] = {
            'estado': 'configurado' if fcm_key_exists else 'no_configurado'
        }
    except Exception as e:
        servicios['fcm'] = {'estado': 'error', 'error': str(e)}
    
    # Prueba de internet
    try:
        response = requests.get('https://httpbin.org/get', timeout=10)
        servicios['internet'] = {
            'estado': 'conectado',
            'status_code': response.status_code
        }
    except Exception as e:
        servicios['internet'] = {'estado': 'error', 'error': str(e)}
    
    logger.info(f"🔧 Prueba de servicios externos: {servicios}")
    return servicios

@shared_task
def prueba_rendimiento_masivo(numero_iteraciones=10):
    """Prueba de rendimiento con múltiples tareas"""
    resultados = []
    
    for i in range(numero_iteraciones):
        resultado = {
            'iteracion': i,
            'timestamp': timezone.now().isoformat(),
            'data_simulada': f"test_data_{i}",
            'procesado': True
        }
        resultados.append(resultado)
    
    logger.info(f"🚀 Prueba de rendimiento completada: {len(resultados)} iteraciones")
    return {
        'total_iteraciones': len(resultados),
        'timestamp_fin': timezone.now().isoformat()
    }