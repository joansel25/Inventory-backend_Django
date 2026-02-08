# apps/productos/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from ..usuario.models import Usuario


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class PrincipioActivo(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Principios Activos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Laboratorio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.pais or 'Sin país'})"


class Producto(models.Model):
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Código único generado automáticamente (PROD-00001)"
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='productos'
    )
    principio_activo = models.ForeignKey(
        PrincipioActivo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='productos'
    )
    laboratorio = models.ForeignKey(
        Laboratorio, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='productos'
    )

    precio_compra = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    precio_venta = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    stock_minimo = models.PositiveIntegerField(default=10)
    stock_actual = models.PositiveIntegerField(default=0, editable=False)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,  # ⚠️ CAMBIO CRÍTICO: permitir blank=True
        editable=False, 
        related_name='productos_creados'
    )

    class Meta:
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion', 'nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
            models.Index(fields=['stock_actual']),
        ]
        permissions = [
            ("puede_ver_reporte_stock", "Puede ver reporte de bajo stock")
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def save(self, *args, **kwargs):
        """
        Genera código automático y asigna creador
        MEJORA: manejo más robusto y profesional
        """
        # Generar código automático solo en creación
        if not self.codigo:
            ultimo = Producto.objects.order_by('-id').first()
            if ultimo and ultimo.codigo.startswith('PROD-'):
                try:
                    numero = int(ultimo.codigo.split('-')[1]) + 1
                except (IndexError, ValueError):
                    numero = 1
            else:
                numero = 1
            self.codigo = f"PROD-{numero:05d}"

        # Asignar creador solo en creación y si se proporciona
        if not self.pk:
            creado_por = kwargs.pop('creado_por', None)
            if creado_por and not self.creado_por:
                self.creado_por = creado_por

        super().save(*args, **kwargs)

    # ✅ CORRECCIÓN: bajo_stock es PROPERTY (sin paréntesis al usar)
    @property
    def bajo_stock(self):
        """Verifica si el producto está en bajo stock"""
        return self.stock_actual <= self.stock_minimo

    @property
    def ganancia_porcentual(self):
        """Calcula el porcentaje de ganancia sobre precio de compra"""
        if self.precio_compra and self.precio_compra > 0:
            return round(
                ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100, 
                2
            )
        return 0

    def estado_stock(self):
        """Retorna el estado textual del stock"""
        if self.stock_actual == 0:
            return "AGOTADO"
        elif self.bajo_stock:  # ⚠️ SIN paréntesis
            return "BAJO"
        return "NORMAL"
    estado_stock.short_description = "Estado Stock"