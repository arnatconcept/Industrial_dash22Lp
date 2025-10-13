import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotask_backend.settings')
django.setup()

from django.urls import get_resolver

print("=== Diagnóstico de URLs ===")

# Verificar todas las URLs registradas
url_conf = get_resolver()
all_urls = []

def list_urls(urlpatterns, base=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            list_urls(pattern.url_patterns, base + str(pattern.pattern))
        else:
            all_urls.append({
                'pattern': base + str(pattern.pattern),
                'name': getattr(pattern, 'name', 'No name')
            })

list_urls(url_conf.url_patterns)

print("URLs registradas:")
for url in all_urls:
    if 'token' in url['pattern']:
        print(f"✓ {url['pattern']} -> {url['name']}")

print("\n=== Fin diagnóstico ===")