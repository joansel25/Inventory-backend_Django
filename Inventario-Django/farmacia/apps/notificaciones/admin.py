# apps/notificaciones/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import NotificacionBajoStock


@admin.register(NotificacionBajoStock)
class NotificacionBajoStockAdmin(admin.ModelAdmin):
    list_display = [
        'fecha_colombiana',
        'producto_link',
        'stock_actual',
        'stock_minimo',
        'urgencia_coloreada',
        'enviada_por_email',
        'leida'
    ]
    list_filter = ['urgencia', 'enviada_por_email', 'leida', 'fecha_creacion']
    search_fields = ['producto__nombre', 'producto__codigo']
    readonly_fields = ['producto', 'stock_actual', 'stock_minimo', 'urgencia', 'fecha_creacion', 'enviada_por_email']
    date_hierarchy = 'fecha_creacion'
    ordering = ['-fecha_creacion']

    def fecha_colombiana(self, obj):
        return timezone.localtime(obj.fecha_creacion).strftime("%d/%m/%Y %I:%M %p")
    fecha_colombiana.short_description = "Fecha y Hora"
    fecha_colombiana.admin_order_field = 'fecha_creacion'

    def producto_link(self, obj):
        url = f"/admin/productos/producto/{obj.producto.id}/change/"
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.producto)
    producto_link.short_description = "Producto"

    def urgencia_coloreada(self, obj):
        colores = {
            'CRÍTICO': 'darkred',
            'URGENTE': 'orange',
            'BAJO': 'blue'
        }
        color = colores.get(obj.urgencia, 'gray')
        return format_html(f'<b style="color:{color}">{obj.get_urgencia_display()}</b>')
    urgencia_coloreada.short_description = "Urgencia"

    def has_add_permission(self, request):
        return False  # Las notificaciones se crean automáticamente

    def has_change_permission(self, request, obj=None):
        return False  # No se editan manualmente