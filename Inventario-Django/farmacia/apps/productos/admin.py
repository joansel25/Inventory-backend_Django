+6# apps/productos/admin.py
from django.contrib import admin
from .models import Categoria, Laboratorio, PrincipioActivo, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'fecha_creacion']
    search_fields = ['nombre']

@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'pais', 'activo']
    search_fields = ['nombre']

@admin.register(PrincipioActivo)
class PrincipioActivoAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'laboratorio', 'stock_actual', 'precio_venta', 'activo']
    list_filter = ['categoria', 'laboratorio', 'activo']
    search_fields = ['nombre', 'codigo']
    readonly_fields = ['codigo', 'stock_actual', 'fecha_creacion', 'creado_por']
    ordering = ['-fecha_creacion']