from django.contrib import admin
from django.urls import path, include, re_path
from api.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from api.views import MobileMotorList, MobileOrdenesAsignadas
from api.admin import custom_admin_site
from django.shortcuts import redirect

# Importar drf_yasg para documentación
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def redirect_to_docs(request):
    return redirect("/swagger/")

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
    path("", redirect_to_docs),
    path('admin/', custom_admin_site.urls),
    path('api/', include('api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('mobile/mis-ordenes/', MobileOrdenesAsignadas.as_view()),

    # Rutas para documentación
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
