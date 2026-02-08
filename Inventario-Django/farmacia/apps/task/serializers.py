# apps/inventory/serializers.py
from rest_framework import serializers
from .models import MovimientoInventario


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    usuario_nombre = serializers.CharField(
        source='usuario.get_full_name', 
        read_only=True,
        default='Sistema'
    )
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    nuevo_stock = serializers.IntegerField(source='producto.stock_actual', read_only=True)
    alerta_bajo_stock = serializers.BooleanField(source='producto.bajo_stock', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_codigo',
            'tipo', 'tipo_display', 'cantidad', 'motivo',
            'usuario', 'usuario_nombre', 'fecha',
            'nuevo_stock', 'alerta_bajo_stock'
        ]
        read_only_fields = ['usuario', 'fecha', 'producto_nombre', 'producto_codigo', 'usuario_nombre', 'tipo_display']

    def create(self, validated_data):
        # Validación de stock para la creación de un nuevo movimiento
        producto = validated_data.get('producto')
        cantidad = validated_data.get('cantidad')
        tipo = validated_data.get('tipo')
        
        producto.refresh_from_db()
        
        if tipo in ['salida', 'ajuste'] and cantidad > producto.stock_actual:
            raise serializers.ValidationError({
                'cantidad': f"Stock insuficiente. Solo hay {producto.stock_actual} unidades disponibles."
            })
        
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Validación de stock para la actualización de un movimiento existente
        producto = instance.producto
        new_cantidad = validated_data.get('cantidad', instance.cantidad)
        new_tipo = validated_data.get('tipo', instance.tipo)

        # Para validar correctamente, debemos calcular el stock disponible *antes* de que el movimiento original se aplicara.
        # 1. Obtenemos el stock actual desde la base de datos.
        producto.refresh_from_db()
        stock_actual_db = producto.stock_actual

        # 2. Revertimos mentalmente el efecto del movimiento *original* para saber con qué contamos.
        stock_disponible_operacion = stock_actual_db
        if instance.tipo == 'entrada':
            stock_disponible_operacion -= instance.cantidad
        elif instance.tipo in ['salida', 'ajuste']:
            stock_disponible_operacion += instance.cantidad

        # 3. Ahora validamos si la *nueva* operación es posible con ese stock.
        if new_tipo in ['salida', 'ajuste'] and new_cantidad > stock_disponible_operacion:
            raise serializers.ValidationError({
                'cantidad': f"Stock insuficiente para esta modificación. El stock disponible para la operación es de {stock_disponible_operacion} unidades."
            })

        # Si la validación es exitosa, procedemos con la actualización normal.
        return super().update(instance, validated_data)