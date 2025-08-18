import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aautotask_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Configurá las credenciales del admin que quieras
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin22')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin22@example.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin22')

# Verifica si ya existe
if not User.objects.filter(username=ADMIN_USERNAME).exists():
    User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD
    )
    print("Superusuario creado ✅")
else:
    print("Superusuario ya existe ✅")
