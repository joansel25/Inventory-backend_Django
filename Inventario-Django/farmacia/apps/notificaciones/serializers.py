# apps/notificaciones/serializers.py
from rest_framework import serializers
from .models import NotificacionBajoStock


class NotificacionBajoStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    categoria = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    urgencia_display = serializers.CharField(source='get_urgencia_display', read_only=True)
    fecha_formateada = serializers.DateTimeField(source='fecha_creacion', format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = NotificacionBajoStock
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_codigo', 'categoria',
            'stock_actual', 'stock_minimo', 'urgencia', 'urgencia_display',
            'mensaje', 'enviada_por_email', 'leida', 'fecha_creacion', 'fecha_formateada'
        ]
        read_only_fields = ['producto', 'stock_actual', 'stock_minimo', 'urgencia', 'enviada_por_email', 'fecha_creacion']