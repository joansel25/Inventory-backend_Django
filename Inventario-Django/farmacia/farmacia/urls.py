from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# Swagger
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.usuario.log_api import LogListAPIView

schema_view = get_schema_view(
    openapi.Info(
        title="Farmacia Inventory API",
        default_version='v1',
        description="Sistema de gestión de inventario para farmacia - TDEA 2025",
        contact=openapi.Contact(email="tuemail@virtual.tdea.edu.co"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    
    path('admin/', admin.site.urls),
    # Autenticación
    path('auth/', include('apps.usuario.urls')), 

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('productos/', include('apps.productos.urls')),     
    path('task/', include('apps.task.urls')),   
    path('notificaciones/', include('apps.notificaciones.urls')),
    path('monitoring/', include('apps.monitoreo.urls')),   

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]