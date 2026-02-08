from django.db.models.signals import post_save
from django.dispatch import receiver
from ..productos.models import Producto
from ..task.models import MovimientoInventario  # ✅ Importar modelo de movimientos
from .models import NotificacionBajoStock


# ✅ SIGNAL PARA CREAR NOTIFICACIÓN TRAS UN MOVIMIENTO DE INVENTARIO
@receiver(post_save, sender=MovimientoInventario)
def revisar_stock_despues_movimiento(sender, instance, created, **kwargs):
    """
    Detecta cuando un movimiento afecta el stock y crea notificación si es necesario
    """
    # Solo procesar movimientos recién creados
    if not created:
        return
    
    # Refrescar el producto para obtener stock actualizado
    producto = instance.producto
    producto.refresh_from_db()  # Obtener el stock actual después del movimiento
    
    # Verificar si ahora está en bajo stock
    if producto.bajo_stock:
        # Se crea la notificación SIEMPRE que haya bajo stock tras un movimiento.
        # Esto garantiza que cada salida crítica envíe su propio correo de alerta.
        NotificacionBajoStock.objects.create(producto=producto)


# ✅ NUEVO SIGNAL PARA ENVIAR EMAIL AL CREAR NOTIFICACIÓN
@receiver(post_save, sender=NotificacionBajoStock)
def enviar_email_notificacion_creada(sender, instance, created, **kwargs):
    """
    Envía un email cuando se crea una nueva notificación de bajo stock.
    """
    if created:
        instance.enviar_email()