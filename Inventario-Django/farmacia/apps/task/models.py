from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..productos.models import Producto
from ..usuario.models import Usuario


from ..productos.lotes_models import Lote

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
    lote = models.ForeignKey(
        Lote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos',
        help_text="Lote afectado por este movimiento"
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
        lote_str = f" (Lote: {self.lote.numero_lote})" if self.lote else ""
        return f"{self.get_tipo_display()} - {self.producto.nombre}{lote_str} ({self.cantidad})"

    def clean(self):
        # Validar stock GLOBAL para Salidas y Ajustes
        if self.tipo in ['salida', 'ajuste'] and self.cantidad > self.producto.stock_actual:
            raise ValidationError(
                f"No hay suficiente stock GLOBAL. Disponible: {self.producto.stock_actual}"
            )
        
        # Validar stock de LOTE si se especifica
        if self.lote and self.tipo in ['salida', 'ajuste']:
            if self.lote.producto != self.producto:
                 raise ValidationError("El lote seleccionado no pertenece al producto.")
            
            if self.cantidad > self.lote.cantidad_actual:
                 raise ValidationError(
                    f"Stock insuficiente en el LOTE {self.lote.numero_lote}. Disponible: {self.lote.cantidad_actual}"
                )

    @transaction.atomic
    def save(self, *args, **kwargs):
        # 1. Si es EDICIÓN, revertir historial
        if self.pk:
            try:
                old_instance = MovimientoInventario.objects.get(pk=self.pk)
                # Revertir Global
                if old_instance.tipo == 'entrada':
                    old_instance.producto.stock_actual -= old_instance.cantidad
                elif old_instance.tipo in ['salida', 'ajuste']:
                    old_instance.producto.stock_actual += old_instance.cantidad
                old_instance.producto.save()

                # Revertir Lote (si tenía)
                if old_instance.lote:
                    if old_instance.tipo == 'entrada':
                        old_instance.lote.cantidad_actual -= old_instance.cantidad
                    elif old_instance.tipo in ['salida', 'ajuste']:
                        old_instance.lote.cantidad_actual += old_instance.cantidad
                    old_instance.lote.save()
                
                if old_instance.producto.pk == self.producto.pk:
                    self.producto.refresh_from_db()
                if self.lote and old_instance.lote and old_instance.lote.pk == self.lote.pk:
                    self.lote.refresh_from_db()

            except MovimientoInventario.DoesNotExist:
                pass

        # 2. Validaciones (Clean ya valida, pero aseguramos)
        if self.tipo in ['salida', 'ajuste']:
             if self.cantidad > self.producto.stock_actual:
                 raise ValidationError(f"No hay suficiente stock. Disponible: {self.producto.stock_actual}")
             if self.lote and self.cantidad > self.lote.cantidad_actual:
                 raise ValidationError(f"Stock insuficiente en lote. Disponible: {self.lote.cantidad_actual}")
        
        # 3. Aplicar NUEVO movimiento Global
        if self.tipo == 'entrada':
            self.producto.stock_actual += self.cantidad
        elif self.tipo in ['salida', 'ajuste']:
            self.producto.stock_actual -= self.cantidad
        self.producto.save()

        # 4. Aplicar NUEVO movimiento a Lote
        if self.lote:
            if self.tipo == 'entrada':
                self.lote.cantidad_actual += self.cantidad
            elif self.tipo in ['salida', 'ajuste']:
                self.lote.cantidad_actual -= self.cantidad
            self.lote.save()

        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        # Revertir Global
        if self.tipo == 'entrada':
            self.producto.stock_actual -= self.cantidad
        elif self.tipo in ['salida', 'ajuste']:
            self.producto.stock_actual += self.cantidad
        self.producto.save()

        # Revertir Lote
        if self.lote:
            if self.tipo == 'entrada':
                self.lote.cantidad_actual -= self.cantidad
            elif self.tipo in ['salida', 'ajuste']:
                self.lote.cantidad_actual += self.cantidad
            self.lote.save()

        super().delete(*args, **kwargs)