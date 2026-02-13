# apps/productos/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import F
from django.utils import timezone
from datetime import timedelta

from ..usuario.permissions import EsAdminOEsFarmaceutico, EsBodeguero
from .models import Categoria, PrincipioActivo, Laboratorio, Producto
from .lotes_models import Ubicacion, Lote
from .serializers import (
    CategoriaSerializer, PrincipioActivoSerializer, LaboratorioSerializer, 
    ProductoSerializer, UbicacionSerializer, LoteSerializer
)
from ..productos.pdf import build_producto_pdf, build_todos_productos_pdf


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated, EsAdminOEsFarmaceutico]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']


class PrincipioActivoViewSet(viewsets.ModelViewSet):
    queryset = PrincipioActivo.objects.all()
    serializer_class = PrincipioActivoSerializer
    permission_classes = [IsAuthenticated, EsAdminOEsFarmaceutico]


class LaboratorioViewSet(viewsets.ModelViewSet):
    queryset = Laboratorio.objects.all()
    serializer_class = LaboratorioSerializer
    permission_classes = [IsAuthenticated, EsAdminOEsFarmaceutico]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related(
        'categoria', 'laboratorio', 'principio_activo'
    ).all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'codigo', 'categoria__nombre', 'laboratorio__nombre']
    ordering_fields = ['nombre', 'stock_actual', 'precio_venta', 'fecha_creacion']
    ordering = ['-fecha_creacion']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), EsAdminOEsFarmaceutico()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        producto = self.get_object()
        pdf = build_producto_pdf(producto)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ficha_{producto.codigo}.pdf"'
        return response

    @action(detail=False, methods=['get'])
    def todos_pdf(self, request):
        productos = self.filter_queryset(self.get_queryset())
        pdf = build_todos_productos_pdf(productos)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="catalogo_farmacia.pdf"'
        return response

    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        productos = self.get_queryset().filter(stock_actual__lte=F('stock_minimo'))
        page = self.paginate_queryset(productos)
        serializer = self.get_serializer(page or productos, many=True)
        return self.get_paginated_response(serializer.data)

class UbicacionViewSet(viewsets.ModelViewSet):
    """
    Gestión de ubicaciones físicas (Estantes, Neveras).
    Acceso: Bodeguero, Farmacéutico, Admin.
    """
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    permission_classes = [IsAuthenticated, EsBodeguero]
    search_fields = ['nombre']

class LoteViewSet(viewsets.ModelViewSet):
    """
    Gestión de lotes y vencimientos.
    Acceso: Bodeguero, Farmacéutico, Admin.
    """
    queryset = Lote.objects.select_related('producto', 'ubicacion').all()
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated, EsBodeguero]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_lote', 'producto__nombre', 'producto__codigo']
    ordering_fields = ['fecha_vencimiento', 'cantidad_actual']

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def por_vencer(self, request):
        """Retorna lotes que vencen en los próximos 90 días"""
        fecha_limite = timezone.now().date() + timedelta(days=90)
        lotes = self.queryset.filter(
            fecha_vencimiento__lte=fecha_limite,
            cantidad_actual__gt=0
        ).order_by('fecha_vencimiento')
        
        page = self.paginate_queryset(lotes)
        serializer = self.get_serializer(page or lotes, many=True)
        return self.get_paginated_response(serializer.data)