# apps/inventory/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
from ..usuario.permissions import *
from .models import MovimientoInventario
from .serializers import MovimientoInventarioSerializer
from ..productos.pdf import build_movimiento_pdf, build_todos_movimientos_pdf


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.select_related(
        'producto__categoria', 'producto__laboratorio', 'usuario'
    ).all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['producto__nombre', 'producto__codigo', 'motivo', 'tipo']
    ordering_fields = ['fecha', 'cantidad', 'tipo']
    ordering = ['-fecha']

    def get_permissions(self):
        # Corregido: Usar un solo permiso que englobe a los roles permitidos (Admin, Farma, Bodeguero)
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), EsBodeguero()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        movimiento = self.get_object()
        pdf_content = build_movimiento_pdf(movimiento)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="movimiento_{movimiento.id}.pdf"'
        return response

    @action(detail=False, methods=['get'], url_path='todos-pdf')
    def todos_pdf(self, request):
        movimientos = self.filter_queryset(self.get_queryset())
        pdf_content = build_todos_movimientos_pdf(movimientos)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="movimientos_completo.pdf"'
        return response

    @action(detail=False, methods=['get'])
    def hoy(self, request):
        hoy = timezone.now().date()
        movimientos = self.get_queryset().filter(fecha__date=hoy)
        page = self.paginate_queryset(movimientos)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)