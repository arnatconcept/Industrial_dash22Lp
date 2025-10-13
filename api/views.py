import os
import logging
import re
from .filters import OrdenMantenimientoFilter

from rest_framework import viewsets, status, filters, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.db.models import Q
from .models import *
from .serializers import *
from .permissions import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Sum, Count, F


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    return Response({
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': getattr(user, 'role', 'Usuario') if hasattr(user, 'role') else 'Usuario'
    })

@login_required
def dashboard_index(request):
    return render(request, "dashboard/index.html")



def produccion_dashboard(request):
    lineas = LineaProduccion.objects.all()
    return render(request, "dashboard/produccion.html", {
        'lineas': lineas
    })
    return render(request, "dashboard/produccion.html")

def reportes_dashboard(request):
    """Vista para el dashboard de reportes"""
    return render(request, "dashboard/reportes.html")


def mantenimiento_dashboard(request):
    return render(request, "dashboard/mantenimiento.html")

def inventario_dashboard(request):
    return render(request, "dashboard/inventario.html")

def ordenes_dashboard(request):
    return render(request, "dashboard/ordenes.html")

def dashboard_fallas(request):
    return render(request, "dashboard/fallas.html")

def alertas_dashboard(request):
    """Vista para el dashboard de alertas"""
    return render(request, "dashboard/alertas.html")




class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def node_red_auth(request):
    """Autenticación simple para Node-RED"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        token = AccessToken.for_user(user)
        return Response({
            'access_token': str(token),
            'user_id': user.id,
            'username': user.username
        })
    
    return Response({'error': 'Credenciales inválidas'}, status=401)

@method_decorator(csrf_exempt, name='dispatch')
class SimpleLoginView(APIView):
    """
    Vista de login simple que evita problemas de CSRF
    """
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Debug: ver qué datos llegan
        print(f"Login attempt - Username: {username}")
        print(f"Request data: {request.data}")
        print(f"Request content type: {request.content_type}")
        
        if not username or not password:
            return Response(
                {'error': 'Username and password required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Autenticar usuario
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_active:
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login exitoso',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        else:
            return Response({
                'success': False,
                'message': 'Credenciales inválidas o usuario inactivo'
            }, status=status.HTTP_401_UNAUTHORIZED)

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 1️⃣ Unidades producidas
        unidades_producidas = ProduccionTurno.objects.filter(
            fecha__range=(start_date, end_date)
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        # 2️⃣ Eficiencia global
        total_planificado = ProduccionTurno.objects.filter(
            fecha__range=(start_date, end_date),
            meta_produccion__isnull=False
        ).aggregate(total=Sum('meta_produccion'))['total'] or 0

        eficiencia_global = round((unidades_producidas / total_planificado) * 100, 2) if total_planificado else 0

        # 3️⃣ Tiempo paradas
        tiempo_paradas = ParadaTurno.objects.filter(
            fecha__range=(start_date, end_date)
        ).aggregate(total=Sum('duracion_minutos'))['total'] or 0

        # 4️⃣ Fallas activas
        fallas_activas = FallaTurno.objects.filter(
            fecha__range=(start_date, end_date)
        ).count()

        return Response({
            'unidades_producidas': unidades_producidas,
            'eficiencia_global': eficiencia_global,
            'tiempo_paradas': tiempo_paradas,
            'fallas_activas': fallas_activas
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

class ReunionDiariaViewSet(viewsets.ModelViewSet):
    queryset = ReunionDiaria.objects.all().order_by('-fecha')
    serializer_class = ReunionDiariaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['estado', 'creada_por']
    search_fields = ['notas', 'motivo_anulacion']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReunionDiariaDetailSerializer
        return ReunionDiariaSerializer
    
    def perform_create(self, serializer):
        serializer.save(creada_por=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        reunion = self.get_object()
        nuevo_estado = request.data.get('estado')
        motivo_anulacion = request.data.get('motivo_anulacion', None)
        
        if nuevo_estado not in dict(ReunionDiaria.ESTADO_CHOICES):
            return Response(
                {'error': 'Estado no válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reunion.estado = nuevo_estado
        if nuevo_estado == 'anulada':
            reunion.motivo_anulacion = motivo_anulacion
        reunion.save()
        
        return Response(ReunionDiariaSerializer(reunion).data)
    
    @action(detail=False, methods=['get'])
    def proximas_reuniones(self, request):
        from datetime import date, timedelta
        hoy = date.today()
        proxima_semana = hoy + timedelta(days=7)
        
        reuniones = ReunionDiaria.objects.filter(
            fecha__gte=hoy, 
            fecha__lte=proxima_semana
        ).order_by('fecha')
        
        page = self.paginate_queryset(reuniones)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reuniones, many=True)
        return Response(serializer.data)


class IncidenciaReunionViewSet(viewsets.ModelViewSet):
    queryset = IncidenciaReunion.objects.all().order_by('-creada_en')
    serializer_class = IncidenciaReunionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo', 'prioridad', 'resuelta', 'reunion']
    search_fields = ['descripcion']
    
    def perform_create(self, serializer):
        serializer.save(reportada_por=self.request.user)
    
    @action(detail=True, methods=['post'])
    def marcar_resuelta(self, request, pk=None):
        incidencia = self.get_object()
        incidencia.resuelta = True
        incidencia.save()
        
        return Response(IncidenciaReunionSerializer(incidencia).data)
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        incidencias = IncidenciaReunion.objects.filter(resuelta=False).order_by('-creada_en')
        
        page = self.paginate_queryset(incidencias)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(incidencias, many=True)
        return Response(serializer.data)


class PlanificacionReunionViewSet(viewsets.ModelViewSet):
    queryset = PlanificacionReunion.objects.all().order_by('-fecha_programada')
    serializer_class = PlanificacionReunionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['reunion', 'responsable']
    search_fields = ['descripcion']
    
    @action(detail=False, methods=['get'])
    def proximas_planificaciones(self, request):
        from datetime import date, timedelta
        hoy = date.today()
        proxima_semana = hoy + timedelta(days=7)
        
        planificaciones = PlanificacionReunion.objects.filter(
            fecha_programada__gte=hoy, 
            fecha_programada__lte=proxima_semana
        ).order_by('fecha_programada')
        
        page = self.paginate_queryset(planificaciones)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(planificaciones, many=True)
        return Response(serializer.data)


class AccionReunionViewSet(viewsets.ModelViewSet):
    queryset = AccionReunion.objects.all().order_by('-fecha_limite')
    serializer_class = AccionReunionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['incidencia', 'completada', 'asignada_a']
    search_fields = ['descripcion']
    
    @action(detail=True, methods=['post'])
    def marcar_completada(self, request, pk=None):
        accion = self.get_object()
        accion.completada = True
        accion.save()
        
        return Response(AccionReunionSerializer(accion).data)
    
    @action(detail=False, methods=['get'])
    def mis_acciones(self, request):
        acciones = AccionReunion.objects.filter(
            asignada_a=request.user, 
            completada=False
        ).order_by('fecha_limite')
        
        page = self.paginate_queryset(acciones)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(acciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        from datetime import date
        hoy = date.today()
        
        acciones = AccionReunion.objects.filter(
            fecha_limite__lt=hoy, 
            completada=False
        ).order_by('fecha_limite')
        
        page = self.paginate_queryset(acciones)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(acciones, many=True)
        return Response(serializer.data)

class TurnoViewSet(viewsets.ModelViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

class ProduccionViewSet(viewsets.ModelViewSet):
    queryset = Produccion.objects.select_related('turno', 'linea', 'supervisor').all()
    serializer_class = ProduccionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['fecha', 'linea', 'turno', 'supervisor', 'producto']
    search_fields = ['producto']  
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros específicos para el dashboard
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        linea_id = self.request.query_params.get('linea')  # Changed from 'linea' to 'linea_id' for clarity
        turno_id = self.request.query_params.get('turno')  # Changed from 'turno' to 'turno_id' for clarity
        supervisor = self.request.query_params.get('supervisor')
        producto = self.request.query_params.get('producto')
        busqueda = self.request.query_params.get('busqueda')
        
        if fecha_desde and fecha_hasta:
            queryset = queryset.filter(fecha__range=[fecha_desde, fecha_hasta])
        elif fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        elif fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        # FIX: Use the string IDs directly, don't try to access .id on strings
        if linea_id:
            queryset = queryset.filter(linea_id=linea_id)  # Use linea_id directly
        if turno_id:
            queryset = queryset.filter(turno_id=turno_id)  # Use turno_id directly
        if supervisor:
            queryset = queryset.filter(supervisor__username__icontains=supervisor)
        if producto:
            queryset = queryset.filter(producto__icontains=producto)
        if busqueda:
            queryset = queryset.filter(
                Q(producto__icontains=busqueda) |
                Q(supervisor__username__icontains=busqueda)
            )
            
        return queryset.order_by('-fecha', '-fecha_creacion')


    def create(self, request, *args, **kwargs):
        print("=== INCOMING REQUEST DATA ===")
        print(f"Data: {request.data}")
        print(f"Content-Type: {request.content_type}")
        print("=============================")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("=== SERIALIZER ERRORS ===")
            print(serializer.errors)
            print("=========================")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"=== ERROR IN PERFORM_CREATE: {str(e)} ===")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        serializer.save()



class ProduccionTurnoViewSet(viewsets.ModelViewSet):
    queryset = ProduccionTurno.objects.all()
    serializer_class = ProduccionTurnoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProduccionTurno.objects.all()
        fecha = self.request.query_params.get('fecha', None)
        linea_id = self.request.query_params.get('linea_id', None)
        turno_id = self.request.query_params.get('turno_id', None)
        
        if fecha:
            queryset = queryset.filter(fecha=fecha)
        if linea_id:
            queryset = queryset.filter(linea_id=linea_id)
        if turno_id:
            queryset = queryset.filter(turno_id=turno_id)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

# views.py - Modificar FallaTurnoViewSet
class FallaTurnoViewSet(viewsets.ModelViewSet):
    queryset = FallaTurno.objects.all()
    serializer_class = FallaTurnoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FallaTurno.objects.all()
        
        # Obtener parámetros de filtro
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        fecha = self.request.query_params.get('fecha', None)  # Mantener compatibilidad
        linea_id = self.request.query_params.get('linea_id', None)
        tipo = self.request.query_params.get('tipo', None)
        gravedad = self.request.query_params.get('gravedad', None)
        turno_id = self.request.query_params.get('turno_id', None)
        busqueda = self.request.query_params.get('busqueda', None)
        
        # Filtro por rango de fechas (prioridad)
        if fecha_desde and fecha_hasta:
            queryset = queryset.filter(fecha__range=[fecha_desde, fecha_hasta])
        elif fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        elif fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        # Mantener compatibilidad con filtro de fecha única
        elif fecha:
            queryset = queryset.filter(fecha=fecha)
            
        # Otros filtros
        if linea_id:
            queryset = queryset.filter(linea_id=linea_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if gravedad:
            queryset = queryset.filter(gravedad=gravedad)
        if turno_id:
            queryset = queryset.filter(turno_id=turno_id)
            
        # Búsqueda en descripción y acción correctiva
        if busqueda:
            queryset = queryset.filter(
                Q(descripcion__icontains=busqueda) | 
                Q(accion_correctiva__icontains=busqueda) |
                Q(equipo__nombre__icontains=busqueda)
            )
            
        return queryset.select_related('linea', 'turno', 'equipo').order_by('-fecha', '-fecha_creacion')
    
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class ParadaTurnoViewSet(viewsets.ModelViewSet):
    queryset = ParadaTurno.objects.all()
    serializer_class = ParadaTurnoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ParadaTurno.objects.all()
        fecha = self.request.query_params.get('fecha', None)
        linea_id = self.request.query_params.get('linea_id', None)
        motivo = self.request.query_params.get('motivo', None)
        
        if fecha:
            queryset = queryset.filter(fecha=fecha)
        if linea_id:
            queryset = queryset.filter(linea_id=linea_id)
        if motivo:
            queryset = queryset.filter(motivo=motivo)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class NodeRedLogViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = NodeRedLog.objects.all()
    serializer_class = NodeRedLogSerializer
    permission_classes = [IsAuthenticated]

# Endpoints para recepción de datos desde Node-RED
@api_view(['POST'])
@permission_classes([AllowAny])
def produccion(request):
    """
    Endpoint para recibir datos de producción desde Node-RED
    """
    serializer = ProduccionSerializer(data=request.data)

    if serializer.is_valid():
        data = serializer.validated_data
        
        try:
            # Verificar que existen los objetos relacionados
            turno = get_object_or_404(Turno, id=data['turno_id'])
            linea = get_object_or_404(LineaProduccion, id=data['linea_id'])
            
            # Crear o actualizar el registro de producción
            produccion, created = Produccion.objects.update_or_create(
                fecha=data['fecha'],
                turno=turno,
                linea=linea,
                defaults={
                    'producto': data['producto'],
                    'bandejas': data.get('bandejas', 0),
                    'fabricacion_toneladas': data.get('fabricacion_toneladas', 0.0),
                    'meta_produccion': data.get('meta_produccion'),
                    'fuente_dato': 'node_red'
                }
            )
            
            # Registrar el log
            NodeRedLog.objects.create(
                tipo_dato='produccion',
                payload=request.data,
                estado='exito',
                mensaje='Registro creado' if created else 'Registro actualizado',
                registros_afectados=1
            )
            
            return Response({'status': 'success', 'created': created}, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Registrar error en el log
            NodeRedLog.objects.create(
                tipo_dato='produccion',
                payload=request.data,
                estado='error',
                mensaje=str(e),
                registros_afectados=0
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        # Registrar error de validación
        NodeRedLog.objects.create(
            tipo_dato='produccion',
            payload=request.data,
            estado='error',
            mensaje=serializer.errors,
            registros_afectados=0
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def node_red_produccion(request):
    """
    Endpoint para recibir datos de producción desde Node-RED
    """
    serializer = NodeRedProduccionSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        
        try:
            # Verificar que existen los objetos relacionados
            turno = get_object_or_404(Turno, id=data['turno_id'])
            linea = get_object_or_404(LineaProduccion, id=data['linea_id'])
            
            # Crear o actualizar el registro de producción
            produccion, created = ProduccionTurno.objects.update_or_create(
                fecha=data['fecha'],
                turno=turno,
                linea=linea,
                defaults={
                    'cantidad': data['cantidad'],
                    'unidad': data.get('unidad', 'unidades'),
                    'meta_produccion': data.get('meta_produccion'),
                    'fuente_dato': 'node_red'
                }
            )
            
            # Registrar el log
            NodeRedLog.objects.create(
                tipo_dato='produccion',
                payload=request.data,
                estado='exito',
                mensaje='Registro creado' if created else 'Registro actualizado',
                registros_afectados=1
            )
            
            return Response({'status': 'success', 'created': created}, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Registrar error en el log
            NodeRedLog.objects.create(
                tipo_dato='produccion',
                payload=request.data,
                estado='error',
                mensaje=str(e),
                registros_afectados=0
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        # Registrar error de validación
        NodeRedLog.objects.create(
            tipo_dato='produccion',
            payload=request.data,
            estado='error',
            mensaje=serializer.errors,
            registros_afectados=0
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def node_red_falla(request):
    """
    Endpoint para recibir datos de fallas desde Node-RED
    """
    serializer = NodeRedFallaSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        
        try:
            # Verificar que existen los objetos relacionados
            turno = get_object_or_404(Turno, id=data['turno_id'])
            linea = get_object_or_404(LineaProduccion, id=data['linea_id'])
            
            # Obtener equipo si se proporciona
            equipo = None
            if data.get('equipo_id'):
                equipo = get_object_or_404(Equipo, id=data['equipo_id'])
            
            # Crear el registro de falla
            falla = FallaTurno.objects.create(
                fecha=data['fecha'],
                turno=turno,
                linea=linea,
                equipo=equipo,
                tipo=data['tipo'],
                gravedad=data.get('gravedad', 'moderada'),
                cantidad=data['cantidad'],
                duracion_minutos=data.get('duracion_minutos', 0),
                descripcion=data.get('descripcion', ''),
                accion_correctiva=data.get('accion_correctiva', ''),
                fuente_dato='node_red'
            )
            
            # Registrar el log
            NodeRedLog.objects.create(
                tipo_dato='falla',
                payload=request.data,
                estado='exito',
                mensaje='Registro creado exitosamente',
                registros_afectados=1
            )
            
            return Response({'status': 'success', 'id': falla.id}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Registrar error en el log
            NodeRedLog.objects.create(
                tipo_dato='falla',
                payload=request.data,
                estado='error',
                mensaje=str(e),
                registros_afectados=0
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        # Registrar error de validación
        NodeRedLog.objects.create(
            tipo_dato='falla',
            payload=request.data,
            estado='error',
            mensaje=serializer.errors,
            registros_afectados=0
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def node_red_parada(request):
    """
    Endpoint para recibir datos de paradas desde Node-RED
    """
    serializer = NodeRedParadaSerializer(data=request.data)
    
    if serializer.is_valid():
        data = serializer.validated_data
        
        try:
            # Verificar que existen los objetos relacionados
            turno = get_object_or_404(Turno, id=data['turno_id'])
            linea = get_object_or_404(LineaProduccion, id=data['linea_id'])
            
            # Obtener equipo si se proporciona
            equipo = None
            if data.get('equipo_id'):
                equipo = get_object_or_404(Equipo, id=data['equipo_id'])
            
            # Crear el registro de parada
            parada = ParadaTurno.objects.create(
                fecha=data['fecha'],
                turno=turno,
                linea=linea,
                equipo=equipo,
                motivo=data['motivo'],
                tipo=data.get('tipo', 'no_programada'),
                duracion_minutos=data['duracion_minutos'],
                descripcion=data.get('descripcion', ''),
                fuente_dato='node_red'
            )
            
            # Registrar el log
            NodeRedLog.objects.create(
                tipo_dato='parada',
                payload=request.data,
                estado='exito',
                mensaje='Registro creado exitosamente',
                registros_afectados=1
            )
            
            return Response({'status': 'success', 'id': parada.id}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Registrar error en el log
            NodeRedLog.objects.create(
                tipo_dato='parada',
                payload=request.data,
                estado='error',
                mensaje=str(e),
                registros_afectados=0
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        # Registrar error de validación
        NodeRedLog.objects.create(
            tipo_dato='parada',
            payload=request.data,
            estado='error',
            mensaje=serializer.errors,
            registros_afectados=0
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)