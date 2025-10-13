#!/usr/bin/env python3
"""
django_project_summary.py
Extrae información esencial de un proyecto Django
para migrarlo a un entorno limpio.
"""

import os
import json
import re

def find_files(base_path, target_filenames):
    """Buscar archivos específicos dentro del proyecto"""
    results = []
    for root, _, files in os.walk(base_path):
        for f in files:
            if f in target_filenames:
                results.append(os.path.join(root, f))
    return results

def extract_installed_apps(settings_path):
    """Extraer INSTALLED_APPS del settings.py"""
    apps = []
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.S)
        if match:
            apps = [a.strip(" '\"\n,") for a in match.group(1).splitlines() if a.strip()]
    except Exception:
        pass
    return apps

def summarize_project(base_path):
    summary = {
        "project_root": base_path,
        "settings_file": None,
        "installed_apps": [],
        "requirements_file": None,
        "apps": [],
        "models_files": [],
        "views_files": [],
        "urls_files": [],
        "templates_folders": [],
        "static_folders": [],
        "migrations": []
    }

    # Buscar settings.py y requirements.txt
    for root, _, files in os.walk(base_path):
        for file in files:
            if file == "settings.py" and "migrations" not in root:
                summary["settings_file"] = os.path.join(root, file)
            elif file == "requirements.txt":
                summary["requirements_file"] = os.path.join(root, file)

    # Obtener INSTALLED_APPS
    if summary["settings_file"]:
        summary["installed_apps"] = extract_installed_apps(summary["settings_file"])

    # Buscar archivos relevantes
    summary["models_files"] = find_files(base_path, ["models.py"])
    summary["views_files"] = find_files(base_path, ["views.py"])
    summary["urls_files"] = find_files(base_path, ["urls.py"])

    # Detectar carpetas templates y static
    for root, dirs, _ in os.walk(base_path):
        for d in dirs:
            if d == "templates":
                summary["templates_folders"].append(os.path.join(root, d))
            elif d == "static":
                summary["static_folders"].append(os.path.join(root, d))
            elif d == "migrations":
                summary["migrations"].append(os.path.join(root, d))

    # Detectar posibles apps (carpetas con __init__.py y models.py)
    apps = []
    for root, dirs, files in os.walk(base_path):
        if "__init__.py" in files and "models.py" in files:
            apps.append(root)
    summary["apps"] = apps

    return summary

if __name__ == "__main__":
    base_path = os.getcwd()
    print("🔍 Analizando proyecto Django en:", base_path)
    info = summarize_project(base_path)

    output_file = os.path.join(base_path, "django_project_summary.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4, ensure_ascii=False)

    print(f"✅ Resumen generado en: {output_file}")
