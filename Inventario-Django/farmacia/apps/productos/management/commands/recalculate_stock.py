from django.core.management.base import BaseCommand
from django.db import transaction
from apps.productos.models import Producto
from apps.task.models import MovimientoInventario

class Command(BaseCommand):
    help = 'Recalcula el stock actual de todos los productos basándose en el historial de movimientos.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando recálculo de stock...")
        
        productos = Producto.objects.all()
        count = 0
        errores = 0
        
        with transaction.atomic():
            for producto in productos:
                # Calcular stock real
                movimientos = MovimientoInventario.objects.filter(producto=producto)
                entradas = 0
                salidas = 0
                
                for mov in movimientos:
                    if mov.tipo == 'entrada':
                        entradas += mov.cantidad
                    elif mov.tipo in ['salida', 'ajuste']:
                        salidas += mov.cantidad
                
                stock_calculado = entradas - salidas
                
                if stock_calculado < 0:
                    self.stdout.write(self.style.ERROR(f"¡ALERTA! Stock negativo calculado para {producto.nombre}: {stock_calculado}. Se ajustará a 0."))
                    stock_calculado = 0

                # Verificar si hay discrepancia
                if producto.stock_actual != stock_calculado:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Discrepancia en {producto.nombre} (Cod: {producto.codigo}): "
                            f"Stock DB: {producto.stock_actual} -> Calculado: {stock_calculado}"
                        )
                    )
                    try:
                        Producto.objects.filter(pk=producto.pk).update(stock_actual=stock_calculado)
                        count += 1
                    except Exception as e:
                         self.stdout.write(self.style.ERROR(f"Error actualizando {producto.nombre}: {e}"))

        
        self.stdout.write(self.style.SUCCESS(f"\nProceso completado. Se corrigieron {count} productos."))
