#!/usr/bin/env python3
"""
rebuild_django_clean.py

Reconstruye un proyecto Django limpio utilizando los datos filtrados del proyecto original.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path

NEW_PROJECT_NAME = "project_clean"  # puedes cambiarlo
DJANGO_APP_NAME = "backend"         # nombre del nuevo proyecto base (settings.py)

def run(cmd):
    """Ejecutar un comando de shell y mostrar salida."""
    print(f"🛠️ Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def copy_if_exists(src, dst):
    """Copia una ruta si existe."""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✅ Copiado: {src} → {dst}")

def copy_tree_if_exists(src, dst):
    """Copia una carpeta completa si existe."""
    if os.path.exists(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"📁 Carpeta copiada: {src} → {dst}")

def main():
    with open("C:\Users\Ary\Documents\import_git\maintech_backend\cleaned_project_summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Crear estructura base
    base_path = Path.cwd() / NEW_PROJECT_NAME
    if base_path.exists():
        print("⚠️ La carpeta del nuevo proyecto ya existe. Eliminando para reconstruir...")
        shutil.rmtree(base_path)
    base_path.mkdir()
    os.chdir(base_path)

    print("🚀 Creando entorno Django limpio...")
    run("python -m venv venv")
    run("venv\\Scripts\\activate && pip install django")

    print("📦 Creando nuevo proyecto Django base...")
    run(f"venv\\Scripts\\activate && django-admin startproject {DJANGO_APP_NAME} .")

    # Copiar apps personalizadas
    apps_dest = base_path
    for app_path in data.get("apps", []):
        app_name = Path(app_path).name
        dest_path = apps_dest / app_name
        copy_tree_if_exists(app_path, dest_path)

    # Copiar templates
    for template_path in data.get("templates_folders", []):
        dest = base_path / "templates" / Path(template_path).name
        copy_tree_if_exists(template_path, dest)

    # Copiar static
    for static_path in data.get("static_folders", []):
        dest = base_path / "static" / Path(static_path).name
        copy_tree_if_exists(static_path, dest)

    # Copiar requirements.txt si existe
    if data.get("requirements_file") and os.path.exists(data["requirements_file"]):
        copy_if_exists(data["requirements_file"], base_path / "requirements.txt")
    else:
        print("⚠️ No se encontró requirements.txt, generando uno vacío.")
        with open(base_path / "requirements.txt", "w", encoding="utf-8") as f:
            f.write("django\n")

    print("\n✅ Proyecto limpio generado correctamente.")
    print("📁 Carpeta creada:", base_path)
    print("\nSiguientes pasos recomendados:")
    print(f"""
    cd {NEW_PROJECT_NAME}
    venv\\Scripts\\activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver
    """)

if __name__ == "__main__":
    main()
