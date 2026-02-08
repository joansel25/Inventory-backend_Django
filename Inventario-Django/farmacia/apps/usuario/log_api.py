from rest_framework import serializers, generics, permissions
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

class LogEntrySerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source='user.username', read_only=True)
    accion = serializers.CharField(source='get_action_flag_display', read_only=True)
    modelo = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = [
            'id', 
            'action_time', 
            'usuario', 
            'content_type', 
            'modelo',
            'object_repr', 
            'accion', 
            'change_message'
        ]

    def get_modelo(self, obj):
        if obj.content_type:
            return obj.content_type.model
        return "Desconocido"

class LogListAPIView(generics.ListAPIView):
    """
    Vista para listar los logs de auditoría del sistema (Django Admin Logs).
    Muestra quién hizo qué cambios en el sistema.
    """
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAdminUser] # Solo admins deberían ver esto

    def get_queryset(self):
        # Ordenar por fecha descendente (lo más nuevo primero)
        return LogEntry.objects.all().select_related('user', 'content_type').order_by('-action_time')
