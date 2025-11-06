from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .notificaciones_views import NotificacionesViewSet, DispositivoView
from . import views

router = DefaultRouter()
router.register(r'turnos', TurnoViewSet)
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
router.register(r'notificaciones', NotificacionesViewSet, basename='notificaciones')
router.register(r'reuniones-diarias', ReunionDiariaViewSet)
router.register(r'incidencias-reunion', IncidenciaReunionViewSet)
router.register(r'planificaciones-reunion', PlanificacionReunionViewSet)
router.register(r'acciones-reunion', AccionReunionViewSet)
router.register(r'produccion', ProduccionViewSet, basename='produccion')

router.register(r'produccion-tiempo-real', ProduccionTiempoRealViewSet, basename='produccion-tiempo-real')

router.register(r'produccion-turno', ProduccionTurnoViewSet, basename='produccionturno') 
router.register(r'fallas-turno', FallaTurnoViewSet, basename='fallaturno') 
router.register(r'paradas-turno', ParadaTurnoViewSet, basename='paradaturno') 
router.register(r'node-red-logs', NodeRedLogViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('user-info/', views.user_info, name='user-info'),
    path('notificaciones/conteo-no-leidas/', NotificacionesViewSet.as_view({'get': 'conteo_no_leidas'}), name='notificaciones-conteo-no-leidas'),
    path('buscar/', BusquedaGlobalView.as_view()),
    path('upload/<str:model_type>/<int:pk>/', UploadFileView.as_view()),
    path('mobile/motores/', MobileMotorList.as_view()),
    path('mobile/mis-ordenes/', MobileOrdenesAsignadas.as_view()),
    #path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('simple-login/', SimpleLoginView.as_view(), name='simple_login'),

    path('node-red/auth/', views.node_red_auth, name='node_red_auth'),
    
    path('first-access/', FirstAccessView.as_view(), name='first_access'),
    path('reportes/inspecciones/', InspeccionReporteView.as_view(), name='reporte-inspecciones'),
    path('ejecuciones-inspeccion/<int:pk>/finalizar/', 
         InspeccionEjecucionViewSet.as_view({'post': 'finalizar'}), 
         name='finalizar-inspeccion'),
    path('dashboard/supervisor/', DashboardSupervisorView.as_view(), name='dashboard-supervisor'),
    path('dashboard/supervisor/variables-top/', DashboardSupervisorVariablesTopView.as_view(), name='dashboard-variables-top'),
    path('dashboard/supervisor/activos-criticos/', DashboardSupervisorActivosCriticosView.as_view(), name='dashboard-activos-criticos'),
    path('dashboard/supervisor/alertas-recientes/', DashboardSupervisorAlertasRecientesView.as_view(), name='dashboard-alertas-recientes'),
    path('dashboard/kpi-inspecciones/', KpiInspeccionesView.as_view(), name='kpi-inspecciones'),


    path('api/node-red/produccion/', views.node_red_produccion, name='node_red_produccion'),
    path('api/node-red/falla/', views.node_red_falla, name='node_red_falla'),
    path('api/node-red/parada/', views.node_red_parada, name='node_red_parada'),

    path('api/dispositivo/registrar/', 
         DispositivoView.as_view(), 
         name='registrar-dispositivo'),

            # Dashboards
    path("dashboard/", dashboard_index, name="dashboard_index"),
    path("dashboard/produccion/", produccion_dashboard, name="produccion_dashboard"),
    path("dashboard/mantenimiento.html", mantenimiento_dashboard, name="mantenimiento_dashboard"),
    path("dashboard/reportes.html", reportes_dashboard, name="reportes_dashboard"),
    path("dashboard/inventario.html", inventario_dashboard, name="inventario_dashboard"),
    path('dashboard/fallas.html', dashboard_fallas, name='dashboard_fallas'),
    path('dashboard/ordnes.html', ordenes_dashboard, name='ordenes_dashboard'),


]
