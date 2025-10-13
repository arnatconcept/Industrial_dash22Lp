from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = "Verifica si un superusuario puede autenticarse en la URL /admin/login/"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, required=True, help="Nombre de usuario")
        parser.add_argument("--password", type=str, required=True, help="Contraseña")
        parser.add_argument("--url", type=str, default="http://127.0.0.1:8000", help="Base URL del proyecto")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        base_url = options["url"]

        login_url = f"{base_url}/admin/login/"
        dashboard_url = f"{base_url}/admin/"

        session = requests.Session()

        # 1. Obtener la página de login para extraer el CSRF token
        resp = session.get(login_url)
        if resp.status_code != 200:
            self.stdout.write(self.style.ERROR(f"No se pudo acceder a {login_url}, status {resp.status_code}"))
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if not csrf:
            self.stdout.write(self.style.ERROR("No se encontró token CSRF en la página de login"))
            return
        csrf_token = csrf["value"]

        # 2. Enviar POST con credenciales
        payload = {
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": csrf_token,
            "next": "/admin/"
        }
        headers = {"Referer": login_url}
        login_resp = session.post(login_url, data=payload, headers=headers)

        # 3. Verificar acceso al admin
        if login_resp.url.startswith(dashboard_url):
            self.stdout.write(self.style.SUCCESS(f"✅ Login exitoso para {username}, acceso confirmado al panel admin"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Login fallido para {username}, revisar credenciales o CSRF"))
            self.stdout.write(f"Redirigió a: {login_resp.url}")
