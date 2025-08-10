import os
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotask_backend.settings") 
django.setup()
import pandas as pd
from django.db import transaction
from django.utils.dateparse import parse_datetime, parse_date
from api import models  # Ajustá si tus modelos están en otra app

def importar_excel_modelo(ruta_excel, model_name):
    df = pd.read_excel(ruta_excel, sheet_name="Datos")
    modelo = getattr(models, model_name)
    errores = []

    for index, fila in df.iterrows():
        try:
            with transaction.atomic():
                datos = {}
                m2m_relaciones = {}

                for campo in fila.index:
                    valor = fila[campo]
                    if pd.isna(valor):
                        continue

                    field_obj = modelo._meta.get_field(campo)

                    if field_obj.many_to_many:
                        m2m_relaciones[campo] = [v.strip() for v in str(valor).split(",")]
                    elif field_obj.is_relation:
                        # Asumimos búsqueda por 'nombre' o 'codigo'
                        rel_model = field_obj.related_model
                        rel_lookup = {}
                        if hasattr(rel_model, 'nombre'):
                            rel_lookup['nombre'] = valor
                        elif hasattr(rel_model, 'codigo'):
                            rel_lookup['codigo'] = valor
                        else:
                            raise ValueError(f"No se pudo determinar el campo de búsqueda para relación '{campo}'")
                        rel_instance = rel_model.objects.filter(**rel_lookup).first()
                        if not rel_instance:
                            raise ValueError(f"No encontrado {rel_model.__name__} con valor '{valor}'")
                        datos[campo] = rel_instance
                    elif field_obj.get_internal_type() == "DateField":
                        datos[campo] = parse_date(str(valor))
                    elif field_obj.get_internal_type() == "DateTimeField":
                        datos[campo] = parse_datetime(str(valor))
                    elif field_obj.get_internal_type() == "IntegerField":
                        datos[campo] = int(valor)
                    else:
                        datos[campo] = valor

                instancia = modelo.objects.create(**datos)

                # ManyToMany
                for campo, codigos in m2m_relaciones.items():
                    rel_model = modelo._meta.get_field(campo).related_model
                    if hasattr(rel_model, 'codigo'):
                        rel_objs = rel_model.objects.filter(codigo__in=codigos)
                    elif hasattr(rel_model, 'nombre'):
                        rel_objs = rel_model.objects.filter(nombre__in=codigos)
                    else:
                        raise ValueError(f"No se puede buscar objetos para ManyToMany '{campo}'")
                    getattr(instancia, campo).set(rel_objs)

        except Exception as e:
            errores.append(f"Fila {index + 2} -> {e}")

    if errores:
        print(f"\nErrores al importar '{model_name}':")
        for err in errores:
            print("  " + err)
    else:
        print(f"Importación de '{model_name}' completada con éxito.")

def importar_todos_los_modelos(input_dir="plantillas_excel"):
    archivos = [f for f in os.listdir(input_dir) if f.endswith(".xlsx")]
    if not archivos:
        print("No se encontraron archivos .xlsx en", input_dir)
        return

    for archivo in archivos:
        model_name = archivo.replace("plantilla_", "").replace(".xlsx", "")
        ruta_excel = os.path.join(input_dir, archivo)
        print(f"\nImportando modelo: {model_name}")
        importar_excel_modelo(ruta_excel, model_name)

if __name__ == "__main__":
    importar_todos_los_modelos()
