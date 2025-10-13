from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

class Command(BaseCommand):
    help = "Verifica superusuarios y prueba autenticación al panel admin"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help="Usuario a probar login")
        parser.add_argument('--password', type=str, help="Contraseña del usuario")

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Superusuarios registrados ==="))
        superusers = User.objects.filter(is_superuser=True)

        if not superusers.exists():
            self.stdout.write(self.style.WARNING(
                "⚠️ No existen superusuarios. Crea uno con: python manage.py createsuperuser"
            ))
        else:
            for su in superusers:
                self.stdout.write(
                    f"- {su.username} ({su.email}) | staff={su.is_staff}, active={su.is_active}, superuser={su.is_superuser}"
                )

        username = kwargs.get('username')
        password = kwargs.get('password')

        if username and password:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== Probando login para {username} ==="))
            user = authenticate(username=username, password=password)
            if user is None:
                self.stdout.write(self.style.ERROR("❌ Credenciales inválidas"))
            elif not user.is_active:
                self.stdout.write(self.style.WARNING("⚠️ Usuario inactivo"))
            elif not user.is_staff:
                self.stdout.write(self.style.WARNING("⚠️ El usuario no tiene permisos de staff → no puede entrar al admin"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Autenticación exitosa, puede ingresar al panel admin"))
