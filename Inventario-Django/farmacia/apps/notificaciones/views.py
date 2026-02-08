# apps/notificaciones/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..usuario.permissions import EsAdmin
from .models import NotificacionBajoStock
from .serializers import NotificacionBajoStockSerializer


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificacionBajoStock.objects.select_related('producto', 'producto__categoria').all()
    serializer_class = NotificacionBajoStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.rol not in ['admin', 'farmaceutico']:
            qs = qs.filter(leida=False)
        return qs.order_by('-fecha_creacion')

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        notif = self.get_object()
        notif.leida = True
        notif.save(update_fields=['leida'])
        return Response({"mensaje": "Notificación marcada como leída"})

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        pendientes = self.get_queryset().filter(leida=False)
        serializer = self.get_serializer(pendientes, many=True)
        return Response({
            "count": pendientes.count(),
            "notificaciones": serializer.data
        })

    @action(detail=False, methods=['get'])
    def por_urgencia(self, request):
        data = {}
        for urgencia, label in NotificacionBajoStock.URGENCIA_CHOICES:
            count = self.get_queryset().filter(urgencia=urgencia).count()
            data[urgencia] = {"label": label, "count": count}
        return Response(data)