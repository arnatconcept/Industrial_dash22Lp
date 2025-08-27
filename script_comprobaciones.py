#!/usr/bin/env python
"""
Script de comprobaciones para el sistema de notificaciones
Ejecutar: python script_comprobaciones.py
"""

import os
import django
import redis
from datetime import timedelta
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotask_backend.settings')
django.setup()

def comprobar_redis():
    """Comprobar conexión a Redis"""
    print("🔍 Comprobando Redis...")
    try:
        from django.conf import settings
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        response = r.ping()
        print("✅ Redis conectado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error de Redis: {e}")
        return False

def comprobar_celery_tasks():
    """Comprobar que las tasks están disponibles"""
    print("\n🔍 Comprobando tasks de Celery...")
    try:
        from api.tasks import (
            verificar_mantenimientos_preventivos,
            recordatorios_ordenes_pendientes,
            reintentar_notificaciones_fallidas
        )
        print("✅ Tasks de Celery importadas correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando tasks: {e}")
        return False

def comprobar_models():
    """Comprobar modelos y datos"""
    print("\n🔍 Comprobando modelos y datos...")
    try:
        from api.models import Motor, Variador, NotificacionApp, DispositivoApp, User
        
        # Estadísticas básicas
        print(f"   Motores: {Motor.objects.count()}")
        print(f"   Variadores: {Variador.objects.count()}")
        print(f"   Notificaciones: {NotificacionApp.objects.count()}")
        print(f"   Dispositivos: {DispositivoApp.objects.count()}")
        print(f"   Usuarios técnicos: {User.objects.filter(role='tecnico').count()}")
        
        # Verificar motores con mantenimiento próximo
        hoy = timezone.now().date()
        motores = Motor.objects.filter(
            proximo_mantenimiento__isnull=False, 
            estado='operativo',
            proximo_mantenimiento__lte=hoy + timedelta(days=7)
        )
        print(f"   Motores con mantenimiento próximo (≤7 días): {motores.count()}")
        
        return True
    except Exception as e:
        print(f"❌ Error en modelos: {e}")
        return False

def comprobar_fcm():
    """Comprobar configuración FCM"""
    print("\n🔍 Comprobando configuración FCM...")
    try:
        from django.conf import settings
        fcm_configured = bool(settings.FCM_SERVER_KEY)
        print(f"✅ FCM_SERVER_KEY configurada: {fcm_configured}")
        return fcm_configured
    except Exception as e:
        print(f"❌ Error FCM: {e}")
        return False

def comprobar_tasks_periodicas():
    """Comprobar tareas periódicas configuradas"""
    print("\n🔍 Comprobando tareas periódicas...")
    try:
        from django_celery_beat.models import PeriodicTask
        tasks = PeriodicTask.objects.all()
        print(f"   Tareas periódicas configuradas: {tasks.count()}")
        for task in tasks:
            print(f"     - {task.name} ({task.schedule})")
        return True
    except Exception as e:
        print(f"❌ Error tareas periódicas: {e}")
        return False

def ejecutar_test_notificacion():
    """Ejecutar una test de notificación"""
    print("\n🔍 Ejecutando test de notificación...")
    try:
        from api.tasks import verificar_mantenimientos_preventivos
        from celery.result import AsyncResult
        from autotask_backend.celery import app
        
        # Ejecutar task
        result = verificar_mantenimientos_preventivos.delay()
        print(f"✅ Task enviada: {result.id}")
        
        # Esperar y verificar resultado
        print("   Esperando resultado...")
        task_result = AsyncResult(result.id, app=app)
        
        # Esperar máximo 30 segundos
        for i in range(30):
            if task_result.ready():
                break
            timezone.sleep(1)
        
        if task_result.ready():
            print(f"✅ Task completada: {task_result.state}")
            if task_result.successful():
                print("✅ Task ejecutada exitosamente")
            else:
                print(f"❌ Task falló: {task_result.result}")
        else:
            print("⚠️  Task aún en ejecución...")
            
        return task_result.successful() if task_result.ready() else False
        
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False

def comprobar_notificaciones_recientes():
    """Comprobar notificaciones recientes"""
    print("\n🔍 Comprobando notificaciones recientes...")
    try:
        from api.models import NotificacionApp
        from django.utils import timezone
        from datetime import timedelta
        
        # Notificaciones de última hora
        una_hora = timezone.now() - timedelta(hours=1)
        recientes = NotificacionApp.objects.filter(fecha_creacion__gte=una_hora)
        
        print(f"   Notificaciones última hora: {recientes.count()}")
        
        if recientes.exists():
            for notif in recientes[:3]:  # Mostrar primeras 3
                print(f"     - {notif.titulo} ({notif.tipo})")
        
        return True
    except Exception as e:
        print(f"❌ Error notificaciones: {e}")
        return False

def crear_datos_prueba():
    """Crear datos de prueba si no existen"""
    print("\n🔍 Creando datos de prueba...")
    try:
        from api.models import Motor, User
        from django.utils import timezone
        from datetime import timedelta
        
        # Crear motor de prueba si no existe
        motor, created = Motor.objects.get_or_create(
            codigo="MOT-TEST-001",
            defaults={
                'estado': 'operativo',
                'proximo_mantenimiento': timezone.now().date() + timedelta(days=3),
                'potencia': '10HP',
                'tipo': 'Prueba',
                'rpm': '1500',
                'brida': 'B14',
                'anclaje': 'Pie'
            }
        )
        
        if created:
            print(f"✅ Motor de prueba creado: {motor.codigo}")
        else:
            print(f"⚠️  Motor de prueba ya existe: {motor.codigo}")
        
        return True
    except Exception as e:
        print(f"❌ Error creando datos prueba: {e}")
        return False

def comprobacion_completa():
    """Ejecutar todas las comprobaciones"""
    print("=" * 60)
    print("🔄 INICIANDO COMPROBACIÓN DEL SISTEMA DE NOTIFICACIONES")
    print("=" * 60)
    
    resultados = []
    
    # Ejecutar comprobaciones
    resultados.append(comprobar_redis())
    resultados.append(comprobar_celery_tasks())
    resultados.append(comprobar_models())
    resultados.append(comprobar_fcm())
    resultados.append(comprobar_tasks_periodicas())
    resultados.append(crear_datos_prueba())
    resultados.append(comprobar_notificaciones_recientes())
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DE LA COMPROBACIÓN")
    print("=" * 60)
    
    exitos = sum(resultados)
    total = len(resultados)
    
    print(f"Comprobaciones exitosas: {exitos}/{total}")
    
    if exitos == total:
        print("🎉 ¡Sistema completamente operativo!")
        # Ejecutar test final
        print("\n🧪 Ejecutando test final...")
        if ejecutar_test_notificacion():
            print("🎉 ¡Test final exitoso!")
        else:
            print("⚠️  Test final con observaciones")
    else:
        print("⚠️  Sistema con observaciones, revisar los errores")
    
    print("=" * 60)

if __name__ == "__main__":
    comprobacion_completa()