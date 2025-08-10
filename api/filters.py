import django_filters
from .models import OrdenMantenimiento

class OrdenMantenimientoFilter(django_filters.FilterSet):
    fecha_creacion_desde = django_filters.DateTimeFilter(field_name='fecha_creacion', lookup_expr='gte')
    fecha_creacion_hasta = django_filters.DateTimeFilter(field_name='fecha_creacion', lookup_expr='lte')

    fecha_cierre_desde = django_filters.DateTimeFilter(field_name='fecha_cierre', lookup_expr='gte')
    fecha_cierre_hasta = django_filters.DateTimeFilter(field_name='fecha_cierre', lookup_expr='lte')

    class Meta:
        model = OrdenMantenimiento
        fields = [
            'estado', 'tipo', 'prioridad', 'operario_asignado', 'creado_por',
            'equipos', 'equipos__sector', 'equipos__sector__linea',
            'motores', 'motores__sector', 'motores__linea',
            'variadores', 'variadores__sector', 'variadores__linea',
        ]
