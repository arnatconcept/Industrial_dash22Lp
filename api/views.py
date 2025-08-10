import os
import logging
import re
from .filters import OrdenMantenimientoFilter

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.db.models import Q
from .models import *
from .serializers import *
from .permissions import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.parsers import MultiPartParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Count, Avg
from django.db.models.functions import Abs
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class FirstAccessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "Primer acceso exitoso"})

class LineaProduccionViewSet(viewsets.ModelViewSet):
    queryset = LineaProduccion.objects.all()
    serializer_class = LineaProduccionSerializer
    filter_backends = [DjangoFilterBackend]
    

class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['linea']  # Filtra por el campo 'linea' (ForeignKey)
    

class EquipoViewSet(viewsets.ModelViewSet):
    queryset = Equipo.objects.all()
    serializer_class = EquipoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sector']  # Filtra por el campo 'sector' (ForeignKey)
    

class DepositoViewSet(viewsets.ModelViewSet):
    queryset = Deposito.objects.all()
    serializer_class = DepositoSerializer
    filter_backends = [DjangoFilterBackend]
    

class MotorViewSet(viewsets.ModelViewSet):
    queryset = Motor.objects.all()
    serializer_class = MotorSerializer
    filterset_fields = ['ubicacion_tipo', 'linea', 'sector', 'equipo']
    parser_classes = [JSONParser, MultiPartParser]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_foto(self, request, pk=None):
        motor = self.get_object()

        if 'file' not in request.FILES:
            return Response({'error': 'No se proporcionó archivo'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']

        logger.debug(f"Subiendo foto: nombre={file.name}, tamaño={file.size}")

        # Validar extensión de imagen
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in valid_extensions:
            return Response({'error': 'Solo se permiten imágenes (JPG, PNG, GIF)'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Eliminar imagen anterior si existe
            if motor.imagen:
                motor.imagen.delete(save=False)

            filename = f"foto_{motor.id}_{file.name}"
            motor.imagen.save(filename, file)

            motor.imagen_url = motor.imagen.url
            motor.save()

            return Response({
                'status': 'success',
                'imagen_url': motor.imagen.url,
                'motor_id': motor.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error al subir foto: {e}")
            return Response({'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_plano(self, request, pk=None):
        motor = self.get_object()

        if 'file' not in request.FILES:
            return Response({'error': 'No se proporcionó archivo'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']

        logger.debug(f"Subiendo plano: nombre={file.name}, tamaño={file.size}")

        # Validar extensión PDF
        ext = os.path.splitext(file.name)[1].lower()
        if ext != '.pdf':
            return Response({'error': 'Solo se permiten archivos PDF'}, status=status.HTTP_400_BAD_REQUEST)

        # Validar encabezado PDF
        file_header = file.read(4)
        file.seek(0)
        if file_header != b'%PDF':
            return Response({'error': 'El archivo no es un PDF válido'}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 20 * 1024 * 1024:
            return Response({'error': 'El archivo es demasiado grande (máximo 20MB)'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            clean_name = re.sub(r'[^\w\.-]', '_', file.name)
            filename = f"plano_{motor.id}_{clean_name}"

            if motor.ref_plano:
                motor.ref_plano.delete(save=False)

            motor.ref_plano.save(filename, file)

            motor.plano_url = motor.ref_plano.url
            motor.save()

            return Response({
                'status': 'success',
                'plano_url': motor.ref_plano.url,
                'motor_id': motor.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error al subir plano: {e}")
            return Response({'error': 'Error interno del servidor'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class VariadorViewSet(viewsets.ModelViewSet):
    queryset = Variador.objects.all()
    serializer_class = VariadorSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_file(self, request, pk=None):
        variador = self.get_object()
        file_field = request.data.get('imagen') or request.data.get('manual')

        if 'imagen' in request.data:
            variador.imagen = request.data['imagen']
        if 'manual' in request.data:
            variador.manual = request.data['manual']

        variador.save()
        return Response(self.get_serializer(variador).data)


    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().prefetch_related('reparacion_set')
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]
    filterset_fields = ['especialidad']
    search_fields = ['nombre', 'contacto', 'email']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ReparacionViewSet(viewsets.ModelViewSet):
    queryset = Reparacion.objects.all().select_related('proveedor', 'creado_por')
    serializer_class = ReparacionSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]
    filterset_fields = ['tipo', 'equipo_type', 'proveedor']
    search_fields = ['descripcion', 'proveedor__nombre']

    def get_queryset(self):
        queryset = super().get_queryset()
        equipo_id = self.request.query_params.get('equipo_id')
        equipo_type = self.request.query_params.get('equipo_type')
        
        if equipo_id and equipo_type:
            queryset = queryset.filter(
                equipo_id=equipo_id,
                equipo_tipo=equipo_type
            )
        return queryset.order_by('-fecha_inicio')

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class OrdenMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = OrdenMantenimiento.objects.all()
    serializer_class = OrdenMantenimientoSerializer
    permission_classes = [IsAuthenticated]

    # Activar el backend de filtros
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrdenMantenimientoFilter  # Usar el filtro personalizado

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.fecha_cierre and not self.request.data.get('skip_event', False):
            for equipo in instance.equipos.all():
                HistorialMantenimiento.objects.create(
                    equipo_tipo='equipo',
                    equipo_id=equipo.id,
                    tipo_evento='mantenimiento',
                    descripcion=f"Orden {instance.titulo} completada",
                    usuario=self.request.user,
                    orden=instance
                )
            for motor in instance.motores.all():
                HistorialMantenimiento.objects.create(
                    equipo_tipo='motor',
                    equipo_id=motor.id,
                    tipo_evento='mantenimiento',
                    descripcion=f"Orden {instance.titulo} completada",
                    usuario=self.request.user,
                    orden=instance
                )
            for variador in instance.variadores.all():
                HistorialMantenimiento.objects.create(
                    equipo_tipo='variador',
                    equipo_id=variador.id,
                    tipo_evento='mantenimiento',
                    descripcion=f"Orden {instance.titulo} completada",
                    usuario=self.request.user,
                    orden=instance
                )

class HistorialCambioOrdenViewSet(viewsets.ModelViewSet):
    queryset = HistorialCambioOrden.objects.all()
    serializer_class = HistorialCambioOrdenSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar_cambio(self, request):
        mutable_data = request.data.copy()
        mutable_data['usuario'] = request.user.id
        
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class HistorialMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = HistorialMantenimiento.objects.all()
    serializer_class = HistorialMantenimientoSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all().select_related('usuario')
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo']
    search_fields = ['descripcion']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por objeto específico si se solicita
        objeto_id = self.request.query_params.get('objeto_id')
        objeto_tipo = self.request.query_params.get('objeto_tipo')
        
        if objeto_id and objeto_tipo:
            queryset = queryset.filter(
                objeto_id=objeto_id,
                tipo=objeto_tipo
            )
            
        return queryset.order_by('-fecha')

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class PLCViewSet(viewsets.ModelViewSet):
    
    queryset = PLC.objects.all().select_related('ubicacion', 'creado_por')
    serializer_class = PLCSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]
    filterset_fields = ['tipo', 'ubicacion']
    search_fields = ['nombre', 'modelo']

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class PLCEntradaSalidaViewSet(viewsets.ModelViewSet):
    queryset = PLCEntradaSalida.objects.all()  # Añade esta línea
    serializer_class = PLCEntradaSalidaSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]
    
    def get_queryset(self):
        queryset = PLCEntradaSalida.objects.select_related('plc')
        plc_id = self.request.query_params.get('plc_id')
        tipo = self.request.query_params.get('tipo')
        etiqueta = self.request.query_params.get('etiqueta')     
        if plc_id:
            queryset = queryset.filter(plc_id=plc_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if etiqueta:
            queryset = queryset.filter(etiqueta__icontains=etiqueta)
            
        return queryset

class PLCLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PLCLog.objects.all()  
    serializer_class = PLCLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo', 'plc'] 
    
    def get_queryset(self):
        return PLCLog.objects.select_related('plc', 'usuario', 'entrada_salida').order_by('-fecha')

class BusquedaGlobalView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.query_params.get('q', '')
        
        resultados = {
            'motores': Motor.objects.filter(
                Q(codigo__icontains=query) | 
                Q(tipo__icontains=query))
                .values('id', 'codigo', 'tipo', 'estado')[:10],
            
            'variadores': Variador.objects.filter(
                Q(codigo__icontains=query) | 
                Q(marca__icontains=query) |
                Q(modelo__icontains=query))
                .values('id', 'codigo', 'marca', 'modelo', 'estado')[:10],
            
            'plcs': PLC.objects.filter(
                Q(nombre__icontains=query) |
                Q(modelo__icontains=query))
                .values('id', 'nombre', 'modelo', 'tipo')[:10],
            
            'entradas_salidas': PLCEntradaSalida.objects.filter(
                Q(etiqueta__icontains=query) |
                Q(direccion__icontains=query) |
                Q(descripcion__icontains=query))
                .select_related('plc')
                .values('id', 'direccion', 'etiqueta', 'tipo', 'plc__nombre')[:20],
            
            'ordenes': OrdenMantenimiento.objects.filter(
                Q(titulo__icontains=query) |
                Q(descripcion__icontains=query))
                .values('id', 'titulo', 'estado', 'prioridad')[:10]
        }
        
        return Response(resultados)

class UploadFileView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]
    
    def post(self, request, model_type, pk):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)
        
        try:
            if model_type == 'motor':
                obj = Motor.objects.get(pk=pk)
                obj.ref_plano = file
            elif model_type == 'variador':
                obj = Variador.objects.get(pk=pk)
                obj.manual = file
            elif model_type == 'plc':
                obj = PLC.objects.get(pk=pk)
                obj.diagrama = file
            else:
                return Response({'error': 'Invalid model type'}, status=400)
            
            obj.save()
            return Response({'status': 'file uploaded'}, status=200)
        
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class MobileMotorList(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        motores = Motor.objects.all().values(
            'id', 
            'codigo', 
            'estado', 
            'ubicacion_tipo',
            'linea__nombre',
            'sector__nombre',
            'equipo__nombre'
        )
        return Response(list(motores))

class MobileOrdenesAsignadas(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        ordenes = OrdenMantenimiento.objects.filter(
            operario_asignado=user,
            estado__in=['asignada', 'en_proceso']
        ).values(
            'id',
            'titulo',
            'descripcion',
            'prioridad',
            'fecha_creacion'
        )
        return Response(list(ordenes))
    
class RutaInspeccionViewSet(viewsets.ModelViewSet):
    queryset = RutaInspeccion.objects.all()
    serializer_class = RutaInspeccionSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
    'activo_tipo': ['exact'],
    'activo_id': ['exact'],
    'creado_por': ['exact'],
    'nombre': ['icontains'],
    'frecuencia_dias': ['gte', 'lte'],
}

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class VariableInspeccionViewSet(viewsets.ModelViewSet):
    queryset = VariableInspeccion.objects.all()
    serializer_class = VariableInspeccionSerializer
    permission_classes = [IsAuthenticated, IsTecnicoOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ruta']

    def get_queryset(self):
        queryset = super().get_queryset()
        ruta_id = self.request.query_params.get('ruta_id')
        if ruta_id:
            queryset = queryset.filter(ruta_id=ruta_id)
        return queryset

class InspeccionEjecucionViewSet(viewsets.ModelViewSet):
    queryset = InspeccionEjecucion.objects.all()
    serializer_class = InspeccionEjecucionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ruta', 'tecnico']

    def perform_create(self, serializer):
        serializer.save(tecnico=self.request.user)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        ejecucion = self.get_object()
        observaciones = request.data.get('observaciones', '')
        
        ejecucion.observaciones = observaciones
        ejecucion.save()
        
        return Response({'status': 'Inspección finalizada'})

class ResultadoInspeccionViewSet(viewsets.ModelViewSet):
    queryset = ResultadoInspeccion.objects.all()
    serializer_class = ResultadoInspeccionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ejecucion', 'variable']

    def perform_create(self, serializer):
        serializer.save(fecha=timezone.now())

class InspeccionReporteView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]
    
    def get(self, request):
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        
        # Filtros
        ruta_id = request.query_params.get('ruta_id')
        days = int(request.query_params.get('days', 30))
        
        # Fechas para el reporte
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Consulta base
        queryset = ResultadoInspeccion.objects.filter(
            fecha__range=(start_date, end_date)
        )
        
        if ruta_id:
            queryset = queryset.filter(ejecucion__ruta_id=ruta_id)
        
        # Datos para el reporte
        report_data = {
            'total_inspecciones': queryset.values('ejecucion').distinct().count(),
            'promedio_valores': queryset.aggregate(
                avg_valor=Avg('valor_medido')
            ),
            'alertas': queryset.annotate(
                desvio=Abs(F('valor_medido') - F('variable__valor_referencia'))
            ).filter(desvio__gt=F('variable__tolerancia')).count()
        } 
        return Response(report_data)
    
class DashboardSupervisorView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    def get(self, request):
        from django.db.models import Count, Avg, F
        from datetime import datetime, timedelta

        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 1️⃣ Alertas activas
        alertas = Evento.objects.filter(
        fecha__range=(start_date, end_date)
        ).count()

        # 2️⃣ % variables fuera de rango
        total_resultados = ResultadoInspeccion.objects.filter(
            fecha__range=(start_date, end_date)
        ).count()
        fuera_rango = ResultadoInspeccion.objects.filter(
            fecha__range=(start_date, end_date)
        ).annotate(
            desvio=Abs(F('valor_medido') - F('variable__valor_referencia'))
        ).filter(desvio__gt=F('variable__tolerancia')).count()

        porcentaje_fuera = (fuera_rango / total_resultados) * 100 if total_resultados else 0

        return Response({
            'alertas': alertas,
            'porcentaje_fuera_rango': porcentaje_fuera
        })
    
class DashboardSupervisorVariablesTopView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        resultados = ResultadoInspeccion.objects.filter(
            fecha__range=(start_date, end_date)
        ).annotate(
            desvio=Abs(F('valor_medido') - F('variable__valor_referencia'))
        ).filter(desvio__gt=F('variable__tolerancia')) \
         .values('variable__nombre') \
         .annotate(total_fuera=Count('id')) \
         .order_by('-total_fuera')[:5]

        return Response(list(resultados))


class DashboardSupervisorActivosCriticosView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        resultados = ResultadoInspeccion.objects.filter(
            fecha__range=(start_date, end_date)
        ).annotate(
            desvio=Abs(F('valor_medido') - F('variable__valor_referencia'))
        ).filter(desvio__gt=F('variable__tolerancia')) \
         .values('ejecucion__ruta__activo_tipo', 'ejecucion__ruta__activo_id') \
         .annotate(alertas=Count('id')) \
         .order_by('-alertas')[:5]

        return Response(list(resultados))


class DashboardSupervisorAlertasRecientesView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        alertas = Evento.objects.all().order_by('-fecha')[:limit]

        data = [{
            'id': alerta.id,
            'tipo': alerta.tipo,
            'descripcion': alerta.descripcion,
            'fecha': alerta.fecha.strftime("%d/%m/%Y %H:%M"),
            'usuario': str(alerta.usuario) if alerta.usuario else None
        } for alerta in alertas]

        return Response(data)

    
class KpiInspeccionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rutas = RutaInspeccion.objects.all()
        ejecuciones = InspeccionEjecucion.objects.all()

        hace_7_dias = timezone.now() - timedelta(days=7)
        ejecuciones_7d = ejecuciones.filter(fecha__gte=hace_7_dias)

        duraciones = []
        for ejec in ejecuciones:
            resultados = ejec.resultados.all()
            if resultados.exists():
                fechas = resultados.values_list('fecha', flat=True)
                if fechas:
                    duracion = (max(fechas) - min(fechas)).total_seconds() / 60
                    duraciones.append(duracion)

        tiempo_promedio = round(sum(duraciones) / len(duraciones), 1) if duraciones else 0.0

        data = {
            "rutas_totales": rutas.count(),
            "ejecuciones_7d": ejecuciones_7d.count(),
            "tiempo_promedio": tiempo_promedio
        }
        return Response(data)