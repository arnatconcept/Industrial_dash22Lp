from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from api.serializers import CustomTokenObtainPairView  # Importar la vista personalizada
from django.conf import settings
from django.conf.urls.static import static
from api.views import MobileMotorList, MobileOrdenesAsignadas
from api.admin import custom_admin_site
from api import views
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

# Importar drf_yasg para documentación
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import SimpleLoginView

def redirect_to_docs(request):
    return redirect("/dashboard/")

#def redirect_to_docs(request):
#    return redirect("/swagger/")

def redirect_to_login(request):
    return redirect('login')

# Configurar el schema view para la documentación
schema_view = get_schema_view(
   openapi.Info(
      title="API Maintech Backend",
      default_version='v1',
      description="Documentación automática de la API con Swagger y ReDoc",
      terms_of_service="https://www.tusitio.com/terms/",
      contact=openapi.Contact(email="contacto@tusitio.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('login', lambda request: redirect('/accounts/login/')),
    path('signin', lambda request: redirect('/accounts/login/')),
    path('sign-in', lambda request: redirect('/accounts/login/')),

    path("login.html", redirect_to_login),
    path("", redirect_to_docs),
    path('admin/', custom_admin_site.urls),
    path('api/simple-login/', SimpleLoginView.as_view(), name='simple_login_direct'),
    
    # ✅ CORREGIDO: Usar la vista personalizada y eliminar duplicación
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('api/', include('api.urls')),

    # Dashboards (HTML templates)
    path("dashboard/", views.dashboard_index, name="dashboard_index"),
    path("dashboard/produccion.html", views.produccion_dashboard, name="produccion_dashboard"),
    path("dashboard/mantenimiento.html", views.mantenimiento_dashboard, name="mantenimiento_dashboard"),
    path("dashboard/reportes.html", views.reportes_dashboard, name="reportes_dashboard"),
    path("dashboard/inventario.html", views.inventario_dashboard, name="inventario_dashboard"),
    path("dashboard/fallas.html", views.dashboard_fallas, name="dashboard_fallas"),
    path("dashboard/ordenes.html", views.ordenes_dashboard, name="ordenes_dashboard"),
    path("dashboard/alertas.html", views.alertas_dashboard, name="alertas_dashboard"),

    path('mobile/mis-ordenes/', MobileOrdenesAsignadas.as_view()),
    path('charts/', include('charts.urls')),

    # Rutas para documentación
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)