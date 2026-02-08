# apps/inventory/admin.py
from django.contrib import admin
from .models import MovimientoInventario

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'tipo', 'producto', 'cantidad', 'usuario', 'motivo_corto']
    list_filter = ['tipo', 'fecha', 'producto__categoria']
    search_fields = ['producto__nombre', 'producto__codigo', 'motivo']
    readonly_fields = ['fecha']
    autocomplete_fields = ['usuario', 'producto']

    def motivo_corto(self, obj):
        return (obj.motivo[:50] + '...') if len(obj.motivo or "") > 50 else obj.motivo
    motivo_corto.short_description = "Motivo"

    def has_delete_permission(self, request, obj=None):
        # Opcional: evitar borrar movimientos (solo admin lo hace con cuidado)
        return request.user.is_superuser