import json
from django.shortcuts import render
from django.core import serializers
from django.db.models import Count, Sum, Q
from api.models import *
from rest_framework.decorators import api_view
from rest_framework.response import Response


def index(request):
    # Obtener parámetros de filtro
    linea_id = request.GET.get('linea', '')
    turno_id = request.GET.get('turno', '')
    fecha = request.GET.get('fecha', '')
    
   
    # Fallas por tipo (con filtros)
    fallas_tipo_query = FallaTurno.objects.all()
    
    if linea_id:
        fallas_tipo_query = fallas_tipo_query.filter(linea_id=linea_id)
    if turno_id:
        fallas_tipo_query = fallas_tipo_query.filter(turno_id=turno_id)
    if fecha:
        fallas_tipo_query = fallas_tipo_query.filter(fecha=fecha)
    
    fallas_tipo = (
        fallas_tipo_query.values("tipo")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # Fallas por gravedad (con filtros)
    fallas_gravedad_query = FallaTurno.objects.all()
    
    if linea_id:
        fallas_gravedad_query = fallas_gravedad_query.filter(linea_id=linea_id)
    if turno_id:
        fallas_gravedad_query = fallas_gravedad_query.filter(turno_id=turno_id)
    if fecha:
        fallas_gravedad_query = fallas_gravedad_query.filter(fecha=fecha)
    
    fallas_gravedad = (
        fallas_gravedad_query.values("gravedad")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # Próximos mantenimientos (con filtros)
    mantenimientos_query = Motor.objects.filter(proximo_mantenimiento__isnull=False)
    
    if linea_id:
        mantenimientos_query = mantenimientos_query.filter(Q(linea_id=linea_id) | Q(ubicacion_tipo='linea', linea_id=linea_id))
    
    mantenimientos = list(
        mantenimientos_query.values("codigo", "proximo_mantenimiento")
        .order_by("proximo_mantenimiento")[:10]
    )

    context = {
        "segment": "charts",
        "fallas_tipo": json.dumps(list(fallas_tipo)),
        "fallas_gravedad": json.dumps(list(fallas_gravedad)),
        "mantenimientos": json.dumps(list(mantenimientos), default=str),
        "lineas": LineaProduccion.objects.all(),
        "turnos": Turno.objects.all(),
        "filtros": {
            "linea": linea_id,
            "turno": turno_id,
            "fecha": fecha
        }
    }
    return render(request, "charts/index.html", context)

@api_view(['GET'])
def dashboard_data(request):
    from datetime import datetime

    linea = request.GET.get('linea')
    turno = request.GET.get('turno')
    fecha = request.GET.get('fecha')

  

    fallas = FallaTurno.objects.all()

    # Solo filtrar si el parámetro existe y no está vacío
    if linea:
        try:
            fallas = fallas.filter(linea_id=int(linea))
        except ValueError:
            pass  # ignorar si no es un número válido

    if turno:
        try:
            fallas = fallas.filter(turno_id=int(turno))
        except ValueError:
            pass

    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            fallas = fallas.filter(fecha=fecha_obj)
        except ValueError:
            pass

    fallas_tipo = fallas.values("tipo").annotate(total=Count("id"))
    fallas_gravedad = fallas.values("gravedad").annotate(total=Count("id"))

    # Mantenimientos con filtros
    mantenimientos_query = Motor.objects.filter(proximo_mantenimiento__isnull=False)
    
    if linea:
        try:
            mantenimientos_query = mantenimientos_query.filter(Q(linea_id=int(linea)) | Q(ubicacion_tipo='linea', linea_id=int(linea)))
        except ValueError:
            pass

    mantenimientos = list(mantenimientos_query.values("codigo", "proximo_mantenimiento").order_by("proximo_mantenimiento")[:10])

    return Response({
      
        "fallas_tipo": list(fallas_tipo),
        "fallas_gravedad": list(fallas_gravedad),
        "mantenimientos": list(mantenimientos)
    })