from django.db import models
from django.utils import timezone
from datetime import timedelta

class Ubicacion(models.Model):
    """
    Define lugares físicos en la farmacia (Estantes, Neveras, Cajones).
    Permite 'datos quemados' (predefinidos) pero es editable.
    """
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej: Estante A, Nevera 2")
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ubicación Física"
        verbose_name_plural = "Ubicaciones Físicas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Lote(models.Model):
    """
    Gestión de lotes y vencimientos asignada al Bodeguero.
    """
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(max_length=50)
    fecha_vencimiento = models.DateField()
    cantidad_actual = models.PositiveIntegerField(default=0)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    
    creado_por = models.ForeignKey('usuario.Usuario', on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('producto', 'numero_lote')
        ordering = ['fecha_vencimiento']
        verbose_name = "Lote de Producto"
        verbose_name_plural = "Lotes de Productos"

    def __str__(self):
        return f"{self.producto.nombre} - Lote {self.numero_lote}"

    @property
    def estado_vencimiento(self):
        if self.fecha_vencimiento < timezone.now().date():
            return "VENCIDO"
        if self.fecha_vencimiento <= timezone.now().date() + timedelta(days=90):
            return "POR VENCER"
        return "OK"