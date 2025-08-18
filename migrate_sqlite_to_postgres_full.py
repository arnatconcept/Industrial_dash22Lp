import os
import django
import psycopg2
import sqlite3
from django.apps import apps
from django.conf import settings

# ===== CONFIG DJANGO =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotask_backend.settings")  # ajusta si tu settings.py está en otra carpeta
django.setup()

# ===== SQLITE CONFIG =====
SQLITE_PATH = os.path.join(settings.BASE_DIR, "db.sqlite3")
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_cursor = sqlite_conn.cursor()

# ===== POSTGRES CONFIG =====
PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://db_maintech_user:zQq6DoJpvLUwI8SyqYjTC8iL28HmVS2a@dpg-d2h5pqvdiees73e6ekjg-a.oregon-postgres.render.com/db_maintech"
)
pg_conn = psycopg2.connect(PG_URL)
pg_cursor = pg_conn.cursor()


def migrate_model(model):
    """Migra datos de un modelo de SQLite a Postgres automáticamente."""
    table = model._meta.db_table
    fields = [f.column for f in model._meta.fields]

    print(f"🔄 Migrando tabla: {table}")

    # Traer datos desde SQLite
    sqlite_cursor.execute(f"SELECT {', '.join(fields)} FROM {table}")
    rows = sqlite_cursor.fetchall()
    if not rows:
        print(f"   ⚠️ No hay datos en {table}")
        return

    # Insertar en Postgres
    placeholders = ", ".join(["%s"] * len(fields))
    insert_query = f'INSERT INTO "{table}" ({", ".join(fields)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;'

    for row in rows:
        try:
            pg_cursor.execute(insert_query, row)
        except Exception as e:
            print(f"   ⚠️ Error insertando en {table}: {e}")

    pg_conn.commit()
    print(f"   ✅ Migrados {len(rows)} registros de {table}")


def main():
    print("🚀 Ejecutando migrate en Postgres...")
    os.system("python manage.py migrate --noinput")

    print("📦 Migrando datos de SQLite a Postgres...")

    # Desactivar temporalmente FK en Postgres
    pg_cursor.execute("SET session_replication_role = 'replica';")

    # Detectar tablas maestras (sin FK)
    master_models = []
    dependent_models = []

    for model in apps.get_models():
        has_fk = any(f.is_relation and f.many_to_one and not f.auto_created for f in model._meta.fields)
        if has_fk:
            dependent_models.append(model)
        else:
            master_models.append(model)

    # Migrar primero las tablas maestras
    for model in master_models:
        migrate_model(model)

    # Después migrar las dependientes
    for model in dependent_models:
        migrate_model(model)

    # Reactivar FK
    pg_cursor.execute("SET session_replication_role = 'origin';")

    print("🎉 Migración completa!")


if __name__ == "__main__":
    main()
