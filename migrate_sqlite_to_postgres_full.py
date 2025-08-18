import os
import shutil
import django
import sqlite3
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.core.management import call_command
from django.core.files import File
from datetime import datetime

# ===== CONFIG DJANGO =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotask_backend.settings")
django.setup()

# ===== SQLITE CONFIG =====
SQLITE_PATH = os.path.join(settings.BASE_DIR, "db.sqlite3")
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# ===== MAPEO DE IDs =====
id_map = {}  # Para relacionar IDs antiguos y nuevos (útil para ManyToMany)


def convert_value(value, field):
    """Convierte valores de SQLite según tipo de campo de Django."""
    from django.db import models
    if value is None:
        return None
    if isinstance(field, (models.DateTimeField, models.DateField)):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return value
    return value


def migrate_model_data(model):
    """Migra datos de un modelo desde SQLite a Postgres usando Django ORM."""
    table = model._meta.db_table
    fields = [f for f in model._meta.fields if f.concrete and not f.auto_created]
    field_names = [f.name for f in fields]

    print(f"🔄 Migrando tabla: {table}")

    # Traer datos de SQLite
    sqlite_cursor.execute(f"SELECT {', '.join(field_names)} FROM {table}")
    rows = sqlite_cursor.fetchall()
    if not rows:
        print(f"   ⚠️ No hay datos en {table}")
        return

    id_map[table] = {}

    for row in rows:
        data = {}
        for f in fields:
            data[f.name] = convert_value(row[f.name], f)

        # Manejo de archivos (FileField / ImageField)
        for f in fields:
            if isinstance(f, (django.db.models.FileField, django.db.models.ImageField)) and data[f.name]:
                file_path = os.path.join(settings.BASE_DIR, data[f.name])
                if os.path.exists(file_path):
                    data[f.name] = File(open(file_path, 'rb'))

        try:
            with transaction.atomic():
                obj = model.objects.create(**data)
                obj.save()
                id_map[table][row['id']] = obj.id
        except Exception as e:
            print(f"   ⚠️ Error insertando en {table}: {e}")

    print(f"   ✅ Migración completa de {table}")


def migrate_many_to_many(model):
    """Migra relaciones ManyToMany desde SQLite a Postgres con mapeo de IDs."""
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
                old_local_id, old_remote_id = row[local_field], row[remote_field]
                new_local_id = id_map[field.model._meta.db_table].get(old_local_id)
                new_remote_id = id_map[field.remote_field.model._meta.db_table].get(old_remote_id)
                if new_local_id and new_remote_id:
                    obj = field.model.objects.get(pk=new_local_id)
                    related_obj = field.remote_field.model.objects.get(pk=new_remote_id)
                    getattr(obj, field.name).add(related_obj)
            except Exception as e:
                print(f"   ⚠️ Error M2M {table}: {e}")

        print(f"   ✅ Migración completa de {table}")


def main():
    print("🚀 Ejecutando migrate en Postgres...")
    call_command('migrate', interactive=False)

    print("📦 Migrando modelos principales...")
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
