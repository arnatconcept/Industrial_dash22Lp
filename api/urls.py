from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'lineas', LineaProduccionViewSet)
router.register(r'sectores', SectorViewSet)
router.register(r'equipos', EquipoViewSet)
router.register(r'depositos', DepositoViewSet)
router.register(r'eventos', EventoViewSet)
router.register(r'motores', MotorViewSet)
router.register(r'variadores', VariadorViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'reparaciones', ReparacionViewSet)
router.register(r'ordenes', OrdenMantenimientoViewSet)
router.register(r'historial', HistorialMantenimientoViewSet)
router.register(r'plcs', PLCViewSet)
router.register(r'plc-io', PLCEntradaSalidaViewSet, basename='plcentradasalida')
router.register(r'plc-logs', PLCLogViewSet, basename='plclog')
router.register(r'users', UserViewSet, basename='user')
router.register(r'historial-orden', HistorialCambioOrdenViewSet, basename='historial-orden')
router.register(r'rutas-inspeccion', RutaInspeccionViewSet, basename='rutainspeccion')
router.register(r'variables-inspeccion', VariableInspeccionViewSet, basename='variableinspeccion')
router.register(r'ejecuciones-inspeccion', InspeccionEjecucionViewSet, basename='inspeccionejecucion')
router.register(r'resultados-inspeccion', ResultadoInspeccionViewSet, basename='resultadoinspeccion')   

urlpatterns = [
    path('', include(router.urls)),
    path('buscar/', BusquedaGlobalView.as_view()),
    path('upload/<str:model_type>/<int:pk>/', UploadFileView.as_view()),
    path('mobile/motores/', MobileMotorList.as_view()),
    path('mobile/mis-ordenes/', MobileOrdenesAsignadas.as_view()),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('first-access/', FirstAccessView.as_view(), name='first_access'),
    path('reportes/inspecciones/', InspeccionReporteView.as_view(), name='reporte-inspecciones'),
    path('ejecuciones-inspeccion/<int:pk>/finalizar/', 
         InspeccionEjecucionViewSet.as_view({'post': 'finalizar'}), 
         name='finalizar-inspeccion'),
    path('dashboard/supervisor/', DashboardSupervisorView.as_view(), name='dashboard-supervisor'),
    path('dashboard/supervisor/variables-top/', DashboardSupervisorVariablesTopView.as_view(), name='dashboard-variables-top'),
    path('dashboard/supervisor/activos-criticos/', DashboardSupervisorActivosCriticosView.as_view(), name='dashboard-activos-criticos'),
    path('dashboard/supervisor/alertas-recientes/', DashboardSupervisorAlertasRecientesView.as_view(), name='dashboard-alertas-recientes'),
    path('dashboard/kpi-inspecciones/', KpiInspeccionesView.as_view(), name='kpi-inspecciones')


]