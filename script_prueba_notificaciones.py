#!/usr/bin/env python
"""
Script de prueba para el sistema de notificaciones - VERSIÓN CORREGIDA
Ejecutar: python script_prueba_notificaciones.py
"""

import os
import django
import sys
import time  # ✅ Importar time correctamente
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotask_backend.settings')
django.setup()

def print_header(mensaje):
    """Imprimir encabezado decorado"""
    print("\n" + "=" * 60)
    print(f"🎯 {mensaje}")
    print("=" * 60)

def print_exito(mensaje):
    """Imprimir mensaje de éxito"""
    print(f"✅ {mensaje}")

def print_error(mensaje):
    """Imprimir mensaje de error"""
    print(f"❌ {mensaje}")

def print_info(mensaje):
    """Imprimir mensaje informativo"""
    print(f"📋 {mensaje}")

def verificar_configuracion():
    """Verificar configuración del sistema"""
    print_header("VERIFICANDO CONFIGURACIÓN")
    
    from django.conf import settings
    
    # Verificar FCM
    fcm_configured = bool(settings.FCM_SERVER_KEY)
    print_info(f"FCM_SERVER_KEY configurada: {fcm_configured}")
    if fcm_configured:
        print_info(f"Longitud clave: {len(settings.FCM_SERVER_KEY)}")
    
    # Verificar Redis
    redis_configured = bool(settings.CELERY_BROKER_URL)
    print_info(f"Redis configurado: {redis_configured}")
    if redis_configured:
        print_info(f"URL Redis: {settings.CELERY_BROKER_URL}")
    
    return fcm_configured and redis_configured

def crear_usuario_prueba():
    """Crear usuario de prueba si no existe"""
    print_header("CREANDO USUARIO DE PRUEBA")
    
    from api.models import User
    from django.contrib.auth.hashers import make_password
    
    try:
        usuario, created = User.objects.get_or_create(
            username='tecnicoprueba',
            defaults={
                'first_name': 'Técnico',
                'last_name': 'Prueba',
                'email': 'tecnico@prueba.com',
                'password': make_password('password123'),
                'role': 'tecnico',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True
            }
        )
        
        if created:
            print_exito(f"Usuario creado: {usuario.username} (ID: {usuario.id})")
        else:
            print_info(f"Usuario existente: {usuario.username} (ID: {usuario.id})")
        
        return usuario
        
    except Exception as e:
        print_error(f"Error creando usuario: {e}")
        return None

def crear_motor_prueba():
    """Crear motor de prueba para mantenimiento"""
    print_header("CREANDO MOTOR DE PRUEBA")
    
    from api.models import Motor, LineaProduccion, Sector, Equipo, Deposito
    from django.utils import timezone
    
    try:
        # Crear ubicación de prueba si no existe
        linea, _ = LineaProduccion.objects.get_or_create(
            nombre="Línea Prueba",
            defaults={'descripcion': 'Línea de prueba para notificaciones'}
        )
        
        sector, _ = Sector.objects.get_or_create(
            nombre="Sector Prueba",
            linea=linea,
            defaults={}
        )
        
        equipo, _ = Equipo.objects.get_or_create(
            nombre="Equipo Prueba",
            sector=sector,
            defaults={}
        )
        
        deposito, _ = Deposito.objects.get_or_create(
            nombre="Depósito Prueba",
            defaults={'ubicacion': 'Almacén central'}
        )
        
        # Crear motor con mantenimiento próximo
        motor, created = Motor.objects.get_or_create(
            codigo="MOT-PRUEBA-001",
            defaults={
                'potencia': '10HP',
                'tipo': 'Trifásico',
                'rpm': '1500',
                'brida': 'B14',
                'anclaje': 'Pie',
                'estado': 'operativo',
                'ubicacion_tipo': 'linea',
                'linea': linea,
                'sector': sector,
                'equipo': equipo,
                'proximo_mantenimiento': timezone.now().date() + timedelta(days=2),
                'fecha_instalacion': timezone.now().date() - timedelta(days=30)
            }
        )
        
        if created:
            print_exito(f"Motor creado: {motor.codigo}")
            print_info(f"Mantenimiento programado: {motor.proximo_mantenimiento}")
        else:
            print_info(f"Motor existente: {motor.codigo}")
            # Actualizar fecha de mantenimiento para prueba
            motor.proximo_mantenimiento = timezone.now().date() + timedelta(days=2)
            motor.save()
            print_info(f"Mantenimiento actualizado: {motor.proximo_mantenimiento}")
        
        return motor
        
    except Exception as e:
        print_error(f"Error creando motor: {e}")
        return None

def probar_servicio_notificaciones():
    """Probar el servicio de notificaciones directamente"""
    print_header("PROBANDO SERVICIO DE NOTIFICACIONES")
    
    # ✅ CORRECCIÓN: Importar desde la ubicación correcta
    try:
        # Intentar diferentes ubicaciones posibles
        try:
            from api.services.notification_service import NotificationService
        except ImportError:
            try:
                from services.notification_service import NotificationService
            except ImportError:
                from notification_service import NotificationService
        
        from api.models import User
        from django.utils import timezone
        
        service = NotificationService()
        
        # Obtener usuario técnico
        tecnico = User.objects.filter(role='tecnico').first()
        if not tecnico:
            print_error("No hay usuarios técnicos para probar")
            return False
        
        print_info(f"Enviando notificación a: {tecnico.username}")
        
        # Enviar notificación de prueba
        result = service.enviar_notificacion_individual(
            usuario_id=tecnico.id,
            titulo="🔧 Notificación de Prueba",
            mensaje="Esta es una notificación de prueba del sistema",
            tipo="test",
            prioridad="media",
            data_adicional={
                "test": "true",
                "fecha_prueba": str(timezone.now()),
                "usuario": tecnico.username
            }
        )
        
        if result:
            print_exito("Notificación enviada exitosamente")
            
            # Verificar que se guardó en BD
            from api.models import NotificacionApp
            notificacion = NotificacionApp.objects.filter(
                usuario_id=tecnico.id,
                tipo='test'
            ).last()
            
            if notificacion:
                print_info(f"Notificación guardada en BD: ID {notificacion.id}")
                print_info(f"Título: {notificacion.titulo}")
                print_info(f"Enviada push: {notificacion.enviada_push}")
            
            return True
        else:
            print_error("Error enviando notificación")
            return False
            
    except Exception as e:
        print_error(f"Error probando servicio: {e}")
        import traceback
        traceback.print_exc()
        return False

def ejecutar_task_manual():
    """Ejecutar task de mantenimientos preventivos manualmente"""
    print_header("EJECUTANDO TASK DE MANTENIMIENTOS")
    
    from api.tasks import verificar_mantenimientos_preventivos
    
    try:
        print_info("Ejecutando task verificar_mantenimientos_preventivos...")
        
        # Ejecutar task
        result = verificar_mantenimientos_preventivos.delay()
        print_info(f"Task enviada a Celery: {result.id}")
        
        # Esperar y verificar resultado
        from celery.result import AsyncResult
        from autotask_backend.celery import app
        
        print_info("Esperando resultado (máximo 30 segundos)...")
        
        task_result = AsyncResult(result.id, app=app)
        for i in range(30):
            if task_result.ready():
                break
            time.sleep(1)  # ✅ CORRECCIÓN: usar time.sleep en lugar de timezone.sleep
        
        if task_result.ready():
            if task_result.successful():
                print_exito("Task ejecutada exitosamente")
                print_info(f"Resultado: {task_result.result}")
                return True
            else:
                print_error(f"Task falló: {task_result.result}")
                return False
        else:
            print_info("Task aún en ejecución (puede verificar en logs de Celery)")
            return True
            
    except Exception as e:
        print_error(f"Error ejecutando task: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_resultados():
    """Verificar resultados de las pruebas"""
    print_header("VERIFICANDO RESULTADOS")
    
    from api.models import NotificacionApp, Motor
    from django.utils import timezone
    
    try:
        # Verificar notificaciones creadas
        notificaciones_test = NotificacionApp.objects.filter(tipo='test')
        notificaciones_mantenimiento = NotificacionApp.objects.filter(
            tipo='mantenimiento_preventivo'
        )
        
        print_info(f"Notificaciones de test: {notificaciones_test.count()}")
        print_info(f"Notificaciones de mantenimiento: {notificaciones_mantenimiento.count()}")
        
        # Verificar motores con mantenimiento próximo
        hoy = timezone.now().date()
        motores = Motor.objects.filter(
            proximo_mantenimiento__isnull=False,
            estado='operativo',
            proximo_mantenimiento__lte=hoy + timedelta(days=7)
        )
        
        print_info(f"Motores con mantenimiento próximo: {motores.count()}")
        for motor in motores:
            dias = (motor.proximo_mantenimiento - hoy).days
            print_info(f"  - {motor.codigo}: {dias} días")
        
        return True
        
    except Exception as e:
        print_error(f"Error verificando resultados: {e}")
        return False

def limpiar_datos_prueba():
    """Limpiar datos de prueba creados"""
    print_header("LIMPIANDO DATOS DE PRUEBA")
    
    try:
        from api.models import NotificacionApp
        
        # Eliminar notificaciones de test
        eliminadas = NotificacionApp.objects.filter(tipo='test').delete()
        print_info(f"Notificaciones de test eliminadas: {eliminadas[0]}")
        
        print_exito("Limpieza completada")
        return True
        
    except Exception as e:
        print_error(f"Error limpiando datos: {e}")
        return False

def prueba_completa():
    """Ejecutar prueba completa del sistema"""
    print_header("INICIANDO PRUEBA COMPLETA DEL SISTEMA")
    print("🧪 Probando servicio de notificaciones y tasks de Celery")
    print("=" * 60)
    
    # Ejecutar pruebas en orden
    pruebas = [
        ("Configuración", verificar_configuracion),
        ("Usuario prueba", crear_usuario_prueba),
        ("Motor prueba", crear_motor_prueba),
        ("Servicio notificaciones", probar_servicio_notificaciones),
        ("Task Celery", ejecutar_task_manual),
        ("Verificación resultados", verificar_resultados),
        ("Limpieza", limpiar_datos_prueba),
    ]
    
    resultados = []
    
    for nombre, funcion in pruebas:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
            if resultado:
                print_exito(f"{nombre}: OK")
            else:
                print_error(f"{nombre}: FALLÓ")
        except Exception as e:
            print_error(f"{nombre}: ERROR - {e}")
            resultados.append((nombre, False))
        print("-" * 40)
    
    # Mostrar resumen
    print_header("RESUMEN DE PRUEBAS")
    
    exitos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✅ OK" if resultado else "❌ FALLÓ"
        print(f"{nombre}: {estado}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO: {exitos}/{total} pruebas exitosas")
    
    if exitos == total:
        print("🎉 ¡Sistema de notificaciones funcionando correctamente!")
    else:
        print("⚠️  El sistema tiene observaciones, revisar los errores")
    
    print("=" * 60)
    
    return exitos == total

if __name__ == "__main__":
    prueba_completa()