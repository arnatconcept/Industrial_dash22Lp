# services/notificaciones_service.py
import firebase_admin
from firebase_admin import messaging
from django.conf import settings

class ServicioNotificaciones:
    def __init__(self):
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
    
    def enviar_notificacion_push(self, notificacion):
        """Enviar notificación push a través de FCM"""
        try:
            # Buscar dispositivos del usuario
            dispositivos = DispositivoApp.objects.filter(
                usuario_id=notificacion.usuario_id,
                esta_activo=True
            )
            
            for dispositivo in dispositivos:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=notificacion.titulo,
                        body=notificacion.mensaje,
                    ),
                    data={
                        'tipo': notificacion.tipo,
                        'prioridad': notificacion.prioridad,
                        'relacion_id': str(notificacion.relacion_id or ''),
                        'relacion_tipo': notificacion.relacion_tipo or '',
                        'fecha_creacion': notificacion.fecha_creacion.isoformat(),
                        **notificacion.data_adicional
                    },
                    token=dispositivo.token_fcm,
                    android=messaging.AndroidConfig(
                        priority='high' if notificacion.prioridad in ['alta', 'critica'] else 'normal'
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound='default',
                                badge=1,
                                content_available=True
                            )
                        )
                    )
                )
                
                response = messaging.send(message)
                notificacion.enviada_push = True
                notificacion.save()
                
                logger.info(f"Notificación enviada: {response}")
                
        except Exception as e:
            notificacion.intentos_envio += 1
            notificacion.error_envio = str(e)
            notificacion.save()
            logger.error(f"Error enviando notificación: {e}")

    def crear_notificacion_revision(self, usuario_id, usuario_nombre, activo, fecha_limite):
        """Crear notificación de próxima revisión"""
        dias_restantes = (fecha_limite - timezone.now().date()).days
        
        notificacion = NotificacionApp.objects.create(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            titulo=f"📋 Revisión Pendiente - {activo.codigo}",
            mensaje=f"El equipo {activo.codigo} requiere revisión. {dias_restantes} días restantes.",
            tipo="revision",
            prioridad="alta" if dias_restantes <= 3 else "media",
            data_adicional={
                'activo_codigo': activo.codigo,
                'activo_nombre': activo.nombre,
                'fecha_limite': fecha_limite.isoformat(),
                'dias_restantes': dias_restantes
            },
            relacion_id=activo.id,
            relacion_tipo='activo'
        )
        
        self.enviar_notificacion_push(notificacion)
        return notificacion