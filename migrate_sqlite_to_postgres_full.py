import os
import django
import psycopg2
import sqlite3
from django.apps import apps
from django.conf import settings
from django.db import transaction

# ===== CONFIG DJANGO =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotask_backend.settings")
django.setup()

# ===== SQLITE CONFIG =====
SQLITE_PATH = os.path.join(settings.BASE_DIR, "db.sqlite3")
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# ===== POSTGRES CONFIG =====
PG_URL = os.environ.get("DATABASE_URL")
pg_conn = psycopg2.connect(PG_URL)
pg_cursor = pg_conn.cursor()


def migrate_model_data(model):
    """Migra datos de un modelo desde SQLite a Postgres usando Django ORM."""
    table = model._meta.db_table
    fields = [f.name for f in model._meta.fields if f.concrete]

    print(f"🔄 Migrando tabla: {table}")

    # Traer datos de SQLite
    sqlite_cursor.execute(f"SELECT {', '.join(fields)} FROM {table}")
    rows = sqlite_cursor.fetchall()
    if not rows:
        print(f"   ⚠️ No hay datos en {table}")
        return 0

    migrated_count = 0
    for row in rows:
        try:
            data = {field: row[field] for field in fields}
            obj = model(**data)
            obj.save()
            migrated_count += 1
        except Exception as e:
            print(f"   ⚠️ Error insertando en {table}: {e}")
    print(f"   ✅ Migrados {migrated_count} registros de {table}")
    return migrated_count


def migrate_many_to_many(model):
    """Migra relaciones ManyToMany desde SQLite a Postgres."""
    for field in model._meta.many_to_many:
        table = field.remote_field.through._meta.db_table
        local_field = field.m2m_field_name()
        remote_field = field.m2m_reverse_field_name()
        print(f"🔄 Migrando M2M: {table}")

        sqlite_cursor.execute(f"SELECT {local_field}, {remote_field} FROM {table}")
        rows = sqlite_cursor.fetchall()
        if not rows:
            print(f"   ⚠️ No hay datos en {table}")
            continue

        for row in rows:
            try:
                obj = field.model.objects.get(pk=row[local_field])
                related_obj = field.remote_field.model.objects.get(pk=row[remote_field])
                getattr(obj, field.name).add(related_obj)
            except Exception as e:
                print(f"   ⚠️ Error M2M {table}: {e}")
        print(f"   ✅ Migración completa de {table}")


def main():
    print("🚀 Ejecutando migrate en Postgres...")
    os.system("python manage.py migrate --noinput")

    print("📦 Migrando modelos principales...")
    # Orden sugerida: primero maestros
    main_models = [
        'User', 'LineaProduccion', 'Sector', 'Equipo', 'Deposito',
        'Proveedor', 'PLC', 'PLCEntradaSalida'
    ]
    for model_name in main_models:
        model = apps.get_model('api', model_name)
        migrate_model_data(model)

    print("📦 Migrando modelos dependientes...")
    dependent_models = [
        'Motor', 'Variador', 'OrdenMantenimiento', 'Reparacion',
        'HistorialCambioOrden', 'HistorialMantenimiento', 'Evento',
        'PLCLog', 'RutaInspeccion', 'VariableInspeccion',
        'InspeccionEjecucion', 'ResultadoInspeccion'
    ]
    for model_name in dependent_models:
        model = apps.get_model('api', model_name)
        migrate_model_data(model)

    print("📦 Migrando relaciones ManyToMany...")
    m2m_models = ['OrdenMantenimiento']
    for model_name in m2m_models:
        model = apps.get_model('api', model_name)
        migrate_many_to_many(model)

    print("🎉 Migración completa!")


if __name__ == "__main__":
    main()
