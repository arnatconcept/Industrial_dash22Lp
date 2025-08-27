import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotask_backend.settings')
django.setup()

from django.db import connection

def reparar_claves_foraneas():
    print("Reparando claves foráneas inconsistentes...")
    
    # Reparar api_motor
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE api_motor 
            SET equipo_id = NULL 
            WHERE equipo_id IS NOT NULL 
            AND equipo_id NOT IN (SELECT id FROM api_equipo)
        """)
        motores_corregidos = cursor.rowcount
        print(f"Motores corregidos: {motores_corregidos}")
    
    # Reparar api_variador (por si acaso)
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE api_variador 
            SET equipo_id = NULL 
            WHERE equipo_id IS NOT NULL 
            AND equipo_id NOT IN (SELECT id FROM api_equipo)
        """)
        variadores_corregidos = cursor.rowcount
        print(f"Variadores corregidos: {variadores_corregidos}")
    
    print("Reparación completada")

if __name__ == "__main__":
    reparar_claves_foraneas()