import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle
from django.utils import timezone
import os

# Config: ruta al modelo
MODEL_PATH = os.path.join('modelo_predictivo.pkl')

# Suponemos que corres esto dentro del entorno Django
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yourproject.settings")
django.setup()

from inspecciones.models import ResultadoInspeccion

# Carga datos históricos
qs = ResultadoInspeccion.objects.all()
df = pd.DataFrame(list(qs.values('valor_medido')))

X = df['valor_medido'].values.reshape(-1, 1)

# Entrena modelo simple de detección de anomalías
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(X)

# Guarda el modelo
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model, f)

print(f'Modelo guardado en {MODEL_PATH}')
