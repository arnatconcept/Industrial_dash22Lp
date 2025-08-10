import pickle
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from inspecciones.models import ResultadoInspeccion, VariableInspeccion, Evento

MODEL_PATH = settings.BASE_DIR / 'modelo_predictivo.pkl'

class Command(BaseCommand):
    help = 'Corre el modelo predictivo de mantenimiento'

    def handle(self, *args, **options):
        # Cargar modelo
        with open(MODEL_PATH, 'rb') as f:
            modelo = pickle.load(f)

        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        qs = ResultadoInspeccion.objects.filter(fecha__range=(start_date, end_date))
        if not qs.exists():
            self.stdout.write(self.style.WARNING('No hay resultados para analizar.'))
            return

        df = pd.DataFrame(list(qs.values('variable_id', 'valor_medido', 'fecha')))
        df['fecha'] = pd.to_datetime(df['fecha'])

        self.stdout.write(self.style.SUCCESS(f'Datos cargados: {len(df)} resultados.'))

        for var_id in df['variable_id'].unique():
            df_var = df[df['variable_id'] == var_id].sort_values('fecha')
            X = df_var['valor_medido'].values.reshape(-1, 1)

            if len(X) < 5:
                continue  # No hay suficiente histórico

            predicciones = modelo.predict(X)
            score = (predicciones == -1).mean()  # % anomalías

            if score > 0.3:  # Umbral configurable
                variable = VariableInspeccion.objects.get(id=var_id)
                Evento.objects.create(
                    tipo='predictivo',
                    descripcion=f"Alerta IA: Variable '{variable.nombre}' muestra {score*100:.1f}% riesgo de anomalía.",
                    usuario=None,
                    objeto_id=variable.ruta.activo_id
                )
                self.stdout.write(self.style.WARNING(
                    f"Alerta IA generada para variable {variable.nombre} ({score*100:.1f}% anomalía)"
                ))

        self.stdout.write(self.style.SUCCESS('Análisis IA completado.'))
