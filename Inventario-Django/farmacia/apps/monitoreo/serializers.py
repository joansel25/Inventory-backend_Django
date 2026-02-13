from rest_framework import serializers
from .models import APIMetric

class APIMetricSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    fecha_formateada = serializers.DateTimeField(source='timestamp', format="%d/%m/%Y %H:%M", read_only=True)
    estado = serializers.SerializerMethodField()

    class Meta:
        model = APIMetric
        fields = '__all__'

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.username
        return "Anónimo"

    def get_estado(self, obj):
        """Mapea el código de estado a las etiquetas que espera el Frontend"""
        if 200 <= obj.codigo_estado < 300:
            return "exito"       # Verde
        elif 400 <= obj.codigo_estado < 500:
            return "advertencia" # Amarillo
        elif 500 <= obj.codigo_estado < 600:
            return "fallo"       # Rojo
        return "info"            # Azul