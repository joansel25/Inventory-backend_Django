from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from datetime import timedelta
from .models import APIMetric
from apps.usuario.models import Usuario
from apps.productos.models import Producto
from apps.task.models import MovimientoInventario
from apps.notificaciones.models import NotificacionBajoStock
from .serializers import APIMetricSerializer

class AuditLogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AuditLogListView(ListAPIView):
    """
    Lista el historial de logs con filtros avanzados.
    """
    permission_classes = [IsAdminUser]
    serializer_class = APIMetricSerializer
    pagination_class = AuditLogPagination

    def get_queryset(self):
        queryset = APIMetric.objects.all().select_related('usuario').order_by('-timestamp')
        
        # --- Filtraciones ---
        
        # 0. Búsqueda General (search param del frontend)
        search = self.request.query_params.get('search')
        if search and search.strip():  # Verifica que no sea una cadena vacía
            queryset = queryset.filter(
                Q(usuario__username__icontains=search) |
                Q(endpoint__icontains=search) |
                Q(mensaje__icontains=search)
            )

        # 1. Por Usuario (username)
        usuario = self.request.query_params.get('usuario')
        if usuario and usuario.strip():
            queryset = queryset.filter(usuario__username__icontains=usuario)
            
        # 2. Por Método (GET, POST, etc.)
        metodo = self.request.query_params.get('metodo')
        if metodo:
            queryset = queryset.filter(metodo=metodo)
            
        # 3. Por Estado (Exitoso, Error Cliente, etc.)
        # Adaptado para recibir filtros del frontend: exito, fallo, advertencia
        estado_filter = self.request.query_params.get('estado')
        if estado_filter:
            if estado_filter == 'exito':
                queryset = queryset.filter(codigo_estado__gte=200, codigo_estado__lt=300)
            elif estado_filter == 'advertencia':
                queryset = queryset.filter(codigo_estado__gte=400, codigo_estado__lt=500)
            elif estado_filter == 'fallo':
                queryset = queryset.filter(codigo_estado__gte=500)
            else:
                # Fallback por si buscan por texto exacto antiguo
                queryset = queryset.filter(estado__icontains=estado_filter)
            
        # 4. Por Rango de Fechas (Soporta date_from/date_to del frontend)
        fecha_inicio = self.request.query_params.get('fecha_inicio') or self.request.query_params.get('date_from')
        fecha_fin = self.request.query_params.get('fecha_fin') or self.request.query_params.get('date_to')
        
        # Validar que no sean cadenas vacías antes de filtrar
        if fecha_inicio and fecha_fin and fecha_inicio.strip() and fecha_fin.strip():
            queryset = queryset.filter(timestamp__range=[fecha_inicio, fecha_fin])
            
        return queryset

class DashboardMetricsView(APIView):
    """
    Endpoint unificado para el Dashboard del Administrador.
    Devuelve KPIs de negocio y métricas de rendimiento técnico.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        # --- 1. Métricas de Negocio ---
        total_users = Usuario.objects.count()
        total_products = Producto.objects.count()
        # Productos con stock <= stock_minimo
        low_stock_products = Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count()
        
        # Movimientos de hoy
        movements_today = MovimientoInventario.objects.filter(fecha__date=now.date()).count()
        
        # Notificaciones sin leer
        pending_notifications = NotificacionBajoStock.objects.filter(leida=False).count()

        # --- 2. Métricas Técnicas (Últimas 24h) ---
        metrics_qs = APIMetric.objects.filter(timestamp__gte=last_24h)
        
        # Promedio de tiempo de respuesta
        avg_response = metrics_qs.aggregate(Avg('tiempo_respuesta_ms'))['tiempo_respuesta_ms__avg'] or 0
        
        # Tasa de errores (Status 4xx o 5xx)
        total_requests = metrics_qs.count()
        error_count = metrics_qs.filter(codigo_estado__gte=400).count()
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

        # Endpoints más lentos (Top 5)
        slowest_endpoints = metrics_qs.values('endpoint', 'metodo').annotate(
            avg_time=Avg('tiempo_respuesta_ms'),
            count=Count('id')
        ).order_by('-avg_time')[:5]

        return Response({
            "kpis_negocio": {
                "total_usuarios": total_users,
                "total_productos": total_products,
                "alertas_stock": low_stock_products,
                "movimientos_hoy": movements_today,
                "notificaciones_pendientes": pending_notifications
            },
            "rendimiento_sistema": {
                "peticiones_24h": total_requests,
                "latencia_promedio_ms": round(avg_response, 2),
                "tasa_errores_porcentaje": round(error_rate, 2),
                "estado_sistema": "Estable" if error_rate < 5 else "Degradado"
            },
            "endpoints_lentos": slowest_endpoints
        })

class FrontendLogView(APIView):
    """
    Endpoint para recibir logs de errores desde el Frontend.
    Evita el error 404 en consola y centraliza los errores de cliente.
    """
    permission_classes = [AllowAny] # Permitir reportar errores incluso si falló el login

    def post(self, request):
        try:
            data = request.data
            user = request.user if request.user.is_authenticated else None
            
            # Mapear datos del frontend a nuestro modelo APIMetric
            # El frontend suele enviar: { message, level, context, ... }
            mensaje = data.get('message') or data.get('error') or "Error reportado desde Frontend"
            url_origen = data.get('url') or "Frontend"
            
            # Guardamos el log
            APIMetric.objects.create(
                usuario=user,
                endpoint=f"CLIENTE: {url_origen}",
                metodo="LOG",
                codigo_estado=500 if "error" in str(data).lower() else 400,
                estado="Fallo Frontend",
                mensaje=str(mensaje)[:500], # Truncar para evitar errores de BD
                tiempo_respuesta_ms=0
            )
            return Response({"status": "log_received"})
        except Exception as e:
            # Fallar silenciosamente para no romper la app del cliente
            return Response({"status": "error_logging"}, status=200)
