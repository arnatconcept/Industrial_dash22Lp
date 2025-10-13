#!/usr/bin/env python3
"""
clean_django_summary.py
Filtra la información útil del resumen generado y recrea
la estructura base de tu proyecto Django en limpio.
"""

import os
import json
import shutil

def is_in_venv(path):
    """Verifica si la ruta pertenece al entorno virtual"""
    return "venv" in path or "site-packages" in path

def clean_summary(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    base = data["project_root"]

    # Filtrar apps, modelos, vistas y urls que no estén en venv
    cleaned = {
        "project_root": base,
        "requirements_file": data.get("requirements_file"),
        "apps": [p for p in data["apps"] if not is_in_venv(p)],
        "models_files": [p for p in data["models_files"] if not is_in_venv(p)],
        "views_files": [p for p in data["views_files"] if not is_in_venv(p)],
        "urls_files": [p for p in data["urls_files"] if not is_in_venv(p)],
        "templates_folders": [p for p in data["templates_folders"] if not is_in_venv(p)],
        "static_folders": [p for p in data["static_folders"] if not is_in_venv(p)],
        "migrations": [p for p in data["migrations"] if not is_in_venv(p)]
    }

    out_file = os.path.join(base, "cleaned_project_summary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=4, ensure_ascii=False)
    print(f"✅ Archivo filtrado generado en: {out_file}")
    return out_file


def recreate_structure(cleaned_json_path, output_dir="new_django_structure"):
    """Crea la estructura base limpia en una nueva carpeta"""
    with open(cleaned_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_base = os.path.join(os.getcwd(), output_dir)
    if os.path.exists(new_base):
        shutil.rmtree(new_base)
    os.makedirs(new_base)

    for app_path in data["apps"]:
        rel_path = os.path.relpath(app_path, data["project_root"])
        os.makedirs(os.path.join(new_base, rel_path), exist_ok=True)

    for folder_list in ["templates_folders", "static_folders"]:
        for path in data[folder_list]:
            rel_path = os.path.relpath(path, data["project_root"])
            os.makedirs(os.path.join(new_base, rel_path), exist_ok=True)

    print(f"📁 Nueva estructura creada en: {new_base}")
    print("Copiá luego tus archivos reales allí (models, views, urls, templates, static).")


if __name__ == "__main__":
    print("🚀 Limpieza y reconstrucción de proyecto Django")
    input_json = "django_project_summary.json"
    cleaned_json = clean_summary(input_json)
    recreate_structure(cleaned_json)
