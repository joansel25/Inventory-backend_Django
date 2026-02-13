from django.urls import path
from .views import AuditLogListView, DashboardMetricsView

urlpatterns = [
    path('audit-logs/', AuditLogListView.as_view(), name='audit-logs'),
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
]