from django.urls import path
from .views import DashboardMetricsView, AuditLogListView

urlpatterns = [
    # Métricas generales (KPIs + Rendimiento)
    path('dashboard/', DashboardMetricsView.as_view(), name='admin-dashboard-metrics'),
    
    # Logs de auditoría (Quién hizo qué) - Nueva vista con filtros
    path('audit-logs/', AuditLogListView.as_view(), name='admin-audit-logs'),
]
