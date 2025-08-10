from django.contrib import admin
from django.urls import path, include
from api.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from api.views import MobileMotorList, MobileOrdenesAsignadas
from api.admin import custom_admin_site


urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('api/', include('api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('mobile/mis-ordenes/', MobileOrdenesAsignadas.as_view()),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)