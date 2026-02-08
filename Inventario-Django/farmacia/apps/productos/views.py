# apps/productos/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import F

from ..usuario.permissions import EsAdminOEsFarmaceutico
from .models import Categoria, PrincipioActivo, Laboratorio, Producto
from .serializers import CategoriaSerializer, PrincipioActivoSerializer, LaboratorioSerializer, ProductoSerializer
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