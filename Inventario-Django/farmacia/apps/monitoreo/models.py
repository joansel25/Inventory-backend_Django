
from django.db import models
from django.conf import settings

class APIMetric(models.Model):
    """Almacena métricas básicas de rendimiento de los endpoints"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    metodo = models.CharField(max_length=10)
    codigo_estado = models.IntegerField()
    estado = models.CharField(max_length=50, default='Desconocido')
    mensaje = models.TextField(null=True, blank=True)
    tiempo_respuesta_ms= models.FloatField(help_text="Tiempo de respuesta en milisegundos")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Métrica de API"
        verbose_name_plural = "Métricas de API"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['codigo_estado']),
            models.Index(fields=['usuario']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.metodo} {self.endpoint} ({self.codigo_estado}) - {self.tiempo_respuesta_ms:.2f}ms"