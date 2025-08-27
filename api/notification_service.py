# services/notification_service.py
from pyfcm import FCMNotification
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import NotificacionApp, DispositivoApp, OrdenMantenimiento, Evento, User, ResultadoInspeccion
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
    
    def _crear_notificacion_db(self, usuario_id, titulo, mensaje, tipo, prioridad, data_adicional=None, relacion_id=None, relacion_tipo=None):
        """Crea registro en base de datos antes de enviar push"""
        try:
            usuario = User.objects.get(id=usuario_id)
            notificacion = NotificacionApp.objects.create(
                usuario_id=usuario_id,
                usuario_nombre=usuario.get_full_name() or usuario.username,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                prioridad=prioridad,
                data_adicional=data_adicional or {},
                relacion_id=relacion_id,
                relacion_tipo=relacion_tipo
            )
            return notificacion
        except User.DoesNotExist:
            logger.error(f"Usuario {usuario_id} no existe para crear notificación")
            return None
        except Exception as e:
            logger.error(f"Error creando notificación: {str(e)}")
            return None
    
    def enviar_notificacion_individual(self, usuario_id, titulo, mensaje, tipo, prioridad='media', data_adicional=None, relacion_id=None, relacion_tipo=None):
        """Envía notificación a un usuario específico"""
        notificacion = self._crear_notificacion_db(usuario_id, titulo, mensaje, tipo, prioridad, data_adicional, relacion_id, relacion_tipo)
        if not notificacion:
            return False
        
        dispositivos = DispositivoApp.objects.filter(usuario_id=usuario_id, esta_activo=True)
        if not dispositivos.exists():
            logger.warning(f"Usuario {usuario_id} no tiene dispositivos activos")
            return False
        
        registration_ids = [d.token_fcm for d in dispositivos]
        
        # Datos para la app
        data_message = {
            "tipo": tipo,
            "prioridad": prioridad,
            "notificacion_id": str(notificacion.id),
            "titulo": titulo,
            "mensaje": mensaje,
            "relacion_id": str(relacion_id) if relacion_id else "",
            "relacion_tipo": relacion_tipo or "",
            "timestamp": str(timezone.now().timestamp()),
            **(data_adicional or {})
        }
        
        try:
            result = self.push_service.notify_multiple_devices(
                registration_ids=registration_ids,
                message_title=titulo,
                message_body=mensaje,
                data_message=data_message,
                sound="default",
                badge=1
            )
            
            # Actualizar estado de envío
            notificacion.enviada_push = True
            notificacion.save()
            
            logger.info(f"Notificación enviada a usuario {usuario_id}: {titulo}")
            return result
            
        except Exception as e:
            notificacion.intentos_envio += 1
            notificacion.error_envio = str(e)
            notificacion.save()
            logger.error(f"Error enviando notificación: {str(e)}")
            return False
    
    def notificar_nueva_orden(self, orden_id):
        """Notifica nueva orden de trabajo"""
        try:
            orden = OrdenMantenimiento.objects.get(id=orden_id)
            if not orden.operario_asignado:
                logger.warning(f"Orden {orden_id} sin operario asignado")
                return False
            
            titulo = "📋 Nueva Orden de Trabajo"
            mensaje = f"{orden.titulo} - Prioridad: {orden.get_prioridad_display()}"
            
            data_adicional = {
                "orden_id": str(orden.id),
                "estado": orden.estado,
                "prioridad": orden.prioridad,
                "tipo_mantenimiento": orden.tipo,
                "tiempo_estimado": str(orden.tiempo_estimado) if orden.tiempo_estimado else ""
            }
            
            return self.enviar_notificacion_individual(
                usuario_id=orden.operario_asignado.id,
                titulo=titulo,
                mensaje=mensaje,
                tipo="orden_trabajo",
                prioridad=orden.prioridad,
                data_adicional=data_adicional,
                relacion_id=orden.id,
                relacion_tipo="orden"
            )
            
        except OrdenMantenimiento.DoesNotExist:
            logger.error(f"Orden {orden_id} no existe")
            return False
    
    def notificar_cambio_estado_orden(self, orden_id, usuario_cambio_id):
        """Notifica cambio de estado de orden"""
        try:
            orden = OrdenMantenimiento.objects.get(id=orden_id)
            
            # Notificar al técnico asignado
            if orden.operario_asignado:
                titulo = "🔄 Orden Actualizada"
                mensaje = f"Orden #{orden.id} - Estado: {orden.get_estado_display()}"
                
                self.enviar_notificacion_individual(
                    usuario_id=orden.operario_asignado.id,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="actualizacion_orden",
                    prioridad="media",
                    data_adicional={
                        "orden_id": str(orden.id),
                        "nuevo_estado": orden.estado,
                        "usuario_cambio_id": str(usuario_cambio_id)
                    },
                    relacion_id=orden.id,
                    relacion_tipo="orden"
                )
            
            # Notificar al creador de la orden (si es diferente)
            if orden.creado_por and orden.creado_por.id != usuario_cambio_id:
                titulo_supervisor = "📊 Orden Modificada"
                mensaje_supervisor = f"Orden #{orden.id} actualizada por el técnico"
                
                self.enviar_notificacion_individual(
                    usuario_id=orden.creado_por.id,
                    titulo=titulo_supervisor,
                    mensaje=mensaje_supervisor,
                    tipo="actualizacion_orden",
                    prioridad="baja",
                    relacion_id=orden.id,
                    relacion_tipo="orden"
                )
                
        except OrdenMantenimiento.DoesNotExist:
            logger.error(f"Orden {orden_id} no existe")
            return False
    
    def notificar_alerta_inspeccion(self, resultado_inspeccion_id):
        """Notifica alerta de inspección"""
        try:
            resultado = ResultadoInspeccion.objects.get(id=resultado_inspeccion_id)
            ejecucion = resultado.ejecucion
            
            # Calcular severidad
            desvio = abs(resultado.valor_medido - resultado.variable.valor_referencia)
            severidad = 'media'
            if desvio > resultado.variable.tolerancia * 2:
                severidad = 'alta'
            elif desvio > resultado.variable.tolerancia * 3:
                severidad = 'critica'
            
            titulo = "⚠️ Alerta de Inspección"
            mensaje = f"{resultado.variable.nombre} fuera de rango: {resultado.valor_medido}"
            
            # Notificar al técnico que hizo la inspección
            if ejecucion.tecnico:
                self.enviar_notificacion_individual(
                    usuario_id=ejecucion.tecnico.id,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="alerta_inspeccion",
                    prioridad=severidad,
                    data_adicional={
                        "variable": resultado.variable.nombre,
                        "valor_medido": str(resultado.valor_medido),
                        "valor_referencia": str(resultado.variable.valor_referencia),
                        "tolerancia": str(resultado.variable.tolerancia),
                        "desvio": str(desvio)
                    },
                    relacion_id=ejecucion.ruta.activo_id,
                    relacion_tipo=ejecucion.ruta.activo_tipo
                )
            
            # Notificar a supervisores
            supervisores = User.objects.filter(role='supervisor', is_active=True)
            for supervisor in supervisores:
                self.enviar_notificacion_individual(
                    usuario_id=supervisor.id,
                    titulo=titulo,
                    mensaje=f"{mensaje} - Reportado por: {ejecucion.tecnico.get_full_name()}",
                    tipo="alerta_inspeccion",
                    prioridad=severidad,
                    relacion_id=ejecucion.ruta.activo_id,
                    relacion_tipo=ejecucion.ruta.activo_tipo
                )
                
        except ResultadoInspeccion.DoesNotExist:
            logger.error(f"ResultadoInspeccion {resultado_inspeccion_id} no existe")
            return False
    
    def notificar_mantenimiento_preventivo(self, equipo_tipo, equipo_id, dias_restantes):
        """Notifica mantenimiento preventivo próximo"""
        try:
            # Obtener el equipo para validar que existe
            if equipo_tipo == 'motor':
                equipo = Motor.objects.get(pk=equipo_id)
            elif equipo_tipo == 'variador':
                equipo = Variador.objects.get(pk=equipo_id)
        except (Motor.DoesNotExist, Variador.DoesNotExist):
            logger.error(f"{equipo_tipo} con ID {equipo_id} no existe")
            return False
        
        titulo = "🛠️ Mantenimiento Preventivo"
        mensaje = f"Mantenimiento programado en {dias_restantes} días"
        
        # Notificar a todos los técnicos
        tecnicos = User.objects.filter(role='tecnico', is_active=True)
        for tecnico in tecnicos:
            self.enviar_notificacion_individual(
                usuario_id=tecnico.id,
                titulo=titulo,
                mensaje=mensaje,
                tipo="mantenimiento_preventivo",
                prioridad="media" if dias_restantes > 3 else "alta",
                data_adicional={
                    "equipo_tipo": equipo_tipo,
                    "equipo_id": str(equipo_id),
                    "equipo_codigo": equipo.codigo, 
                    "dias_restantes": str(dias_restantes)
                },
                relacion_id=equipo_id,
                relacion_tipo=equipo_tipo
            )