from rest_framework import serializers
from .models import APIMetric

class APIMetricSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    fecha_formateada = serializers.DateTimeField(source='timestamp', format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = APIMetric
        fields = '__all__'

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.username
        return "Anónimo"