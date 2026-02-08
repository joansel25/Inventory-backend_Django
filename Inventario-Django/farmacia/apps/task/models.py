from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..productos.models import Producto
from ..usuario.models import Usuario


class MovimientoInventario(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    )

    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT, 
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    motivo = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='movimientos_realizados'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['producto', '-fecha']),
            models.Index(fields=['tipo', '-fecha']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} ({self.cantidad})"

    def clean(self):
        # Validar stock para Salidas y Ajustes
        if self.tipo in ['salida', 'ajuste'] and self.cantidad > self.producto.stock_actual:
            raise ValidationError(
                f"No hay suficiente stock. Disponible: {self.producto.stock_actual}"
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        # 1. Si es EDICIÓN, primero revertimos el efecto del movimiento anterior
        if self.pk:
            try:
                old_instance = MovimientoInventario.objects.get(pk=self.pk)
                # Revertir: Si era entrada, restamos. Si era salida/ajuste, sumamos.
                if old_instance.tipo == 'entrada':
                    old_instance.producto.stock_actual -= old_instance.cantidad
                elif old_instance.tipo in ['salida', 'ajuste']:
                    old_instance.producto.stock_actual += old_instance.cantidad
                
                old_instance.producto.save()
                
                # Refrescar el producto actual para tener el dato correcto antes de aplicar el nuevo cambio
                if old_instance.producto.pk == self.producto.pk:
                    self.producto.refresh_from_db()
            except MovimientoInventario.DoesNotExist:
                pass

        # 2. Validar el nuevo movimiento (con el stock actualizado tras la reversión)
        # Nota: clean() valida, pero aquí aseguramos la lógica antes de guardar
        if self.tipo in ['salida', 'ajuste'] and self.cantidad > self.producto.stock_actual:
             raise ValidationError(f"No hay suficiente stock. Disponible: {self.producto.stock_actual}")
        
        # 3. Aplicar el NUEVO movimiento
        if self.tipo == 'entrada':
            self.producto.stock_actual += self.cantidad
        elif self.tipo in ['salida', 'ajuste']:
            self.producto.stock_actual -= self.cantidad
        
        self.producto.save() # Esto dispara las alertas de bajo stock si corresponde
        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        # Revertir el efecto al ELIMINAR un movimiento
        if self.tipo == 'entrada':
            self.producto.stock_actual -= self.cantidad
        elif self.tipo in ['salida', 'ajuste']:
            self.producto.stock_actual += self.cantidad
        
        self.producto.save()
        super().delete(*args, **kwargs)