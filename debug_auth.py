import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotask_backend.settings')
django.setup()

from django.test import RequestFactory
from api.views import SimpleLoginView
from io import BytesIO
import json

print("=== Debug Profundo ===")

# Crear una request simulada
factory = RequestFactory()

# Simular request JSON
json_data = json.dumps({'username': 'admin123', 'password': 'admin123'})
request = factory.post(
    '/api/simple-login/',
    data=json_data,
    content_type='application/json'
)

# Probar la vista directamente
view = SimpleLoginView()
view.request = request

try:
    response = view.post(request)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("=== Fin Debug ===")