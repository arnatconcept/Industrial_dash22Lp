import requests
import json

print("=== Prueba JWT después de corrección ===")

# Probar con form-data (debería funcionar ahora)
url = 'http://localhost:8000/api/token/'

# Enfoque 1: Form-data
print("--- Probando con Form-data ---")
response = requests.post(url, data={
    'username': 'admin123',
    'password': 'admin123'
})

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ LOGIN EXITOSO con Form-data!")
    tokens = response.json()
    print(f"Access Token: {tokens.get('access')[:50]}...")
else:
    print(f"Error: {response.text}")

# Enfoque 2: JSON (puede seguir fallando por CSRF)
print("\n--- Probando con JSON ---")
headers = {'Content-Type': 'application/json'}
response = requests.post(url, json={
    'username': 'admin123',
    'password': 'admin123'
}, headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ LOGIN EXITOSO con JSON!")
    tokens = response.json()
    print(f"Access Token: {tokens.get('access')[:50]}...")
else:
    print(f"Error: {response.text}")

print("=== Fin prueba ===")