# test_celery.py
import os
import django
from celery import current_app

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotask_backend.settings')
django.setup()

from api.tasks import tarea_prueba_celery, prueba_servicios_externos, prueba_rendimiento_masivo

def ejecutar_pruebas_celery():
    """Ejecuta todas las pruebas de Celery manualmente"""
    
    print("🧪 INICIANDO PRUEBAS DE CELERY...")
    
    # 1. Prueba básica
    print("1. Ejecutando tarea de prueba básica...")
    resultado1 = tarea_prueba_celery.delay("Mensaje de prueba desde consola")
    print(f"   Tarea ID: {resultado1.id}")
    
    # 2. Prueba de servicios externos
    print("2. Ejecutando prueba de servicios externos...")
    resultado2 = prueba_servicios_externos.delay()
    print(f"   Tarea ID: {resultado2.id}")
    
    # 3. Prueba de rendimiento (pequeña)
    print("3. Ejecutando prueba de rendimiento...")
    resultado3 = prueba_rendimiento_masivo.delay(10)
    print(f"   Tarea ID: {resultado3.id}")
    
    # Esperar resultados
    print("\n⏳ Esperando resultados...")
    
    try:
        res1 = resultado1.get(timeout=30)
        print(f"✅ Tarea 1 completada: {res1.get('estado', 'desconocido')}")
    except Exception as e:
        print(f"❌ Error en tarea 1: {e}")
    
    try:
        res2 = resultado2.get(timeout=30)
        print(f"✅ Tarea 2 completada: {res2}")
    except Exception as e:
        print(f"❌ Error en tarea 2: {e}")
    
    try:
        res3 = resultado3.get(timeout=30)
        print(f"✅ Tarea 3 completada: {res3.get('total_iteraciones', 0)} iteraciones")
    except Exception as e:
        print(f"❌ Error en tarea 3: {e}")
    
    print("\n📊 Verifica los logs para más detalles.")

def verificar_workers_celery():
    """Verifica el estado de los workers de Celery"""
    try:
        inspect = current_app.control.inspect()
        
        # Verificar workers activos
        active_workers = inspect.active()
        if active_workers:
            print("✅ Workers activos encontrados:")
            for worker, tasks in active_workers.items():
                print(f"   {worker}: {len(tasks)} tareas activas")
        else:
            print("⚠️ No hay workers activos")
        
        # Verificar workers registrados
        registered_workers = inspect.registered()
        if registered_workers:
            print("✅ Workers registrados:")
            for worker, tasks in registered_workers.items():
                print(f"   {worker}: {len(tasks)} tareas registradas")
        
        # Verificar estadísticas
        stats = inspect.stats()
        if stats:
            print("📊 Estadísticas de workers:")
            for worker, stat in stats.items():
                print(f"   {worker}: {stat}")
                
    except Exception as e:
        print(f"❌ Error al verificar workers: {e}")

if __name__ == "__main__":
    verificar_workers_celery()
    print("\n" + "="*50)
    ejecutar_pruebas_celery()