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
    lote_numero = serializers.CharField(source='lote.numero_lote', read_only=True)
    
    nuevo_stock = serializers.IntegerField(source='producto.stock_actual', read_only=True)
    alerta_bajo_stock = serializers.BooleanField(source='producto.bajo_stock', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_codigo',
            'lote', 'lote_numero',
            'tipo', 'tipo_display', 'cantidad', 'motivo',
            'usuario', 'usuario_nombre', 'fecha',
            'nuevo_stock', 'alerta_bajo_stock'
        ]
        read_only_fields = ['usuario', 'fecha', 'producto_nombre', 'producto_codigo', 'usuario_nombre', 'tipo_display', 'lote_numero']

    def create(self, validated_data):
        # Validación de stock para la creación de un nuevo movimiento
        producto = validated_data.get('producto')
        cantidad = validated_data.get('cantidad')
        tipo = validated_data.get('tipo')
        lote = validated_data.get('lote')
        
        producto.refresh_from_db()
        
        if tipo in ['salida', 'ajuste']:
             # Validar Global
             if cantidad > producto.stock_actual:
                raise serializers.ValidationError({
                    'cantidad': f"Stock insuficiente en '{producto.nombre}' (ID: {producto.id}). Tienes {producto.stock_actual}, intentas sacar {cantidad}."
                })
             # Validar Lote
             if lote:
                 lote.refresh_from_db()
                 if lote.producto != producto:
                     raise serializers.ValidationError({'lote': 'El lote no pertenece al producto.'})
                 if cantidad > lote.cantidad_actual:
                     raise serializers.ValidationError({
                        'cantidad': f"Stock insuficiente en lote '{lote.numero_lote}'. Tienes {lote.cantidad_actual}, intentas sacar {cantidad}."
                     })
        
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Validación de stock para la actualización de un movimiento existente
        producto = instance.producto
        new_cantidad = validated_data.get('cantidad', instance.cantidad)
        new_tipo = validated_data.get('tipo', instance.tipo)
        new_lote = validated_data.get('lote', instance.lote)

        # Para validar correctamente, debemos calcular el stock disponible *antes* de que el movimiento original se aplicara.
        # 1. Obtenemos el stock actual desde la base de datos.
        producto.refresh_from_db()
        stock_actual_db = producto.stock_actual
        
        stock_lote_db = 0
        if new_lote:
             new_lote.refresh_from_db()
             stock_lote_db = new_lote.cantidad_actual

        # 2. Revertimos mentalmente el efecto del movimiento *original* para saber con qué contamos.
        stock_disponible_operacion = stock_actual_db
        stock_disponible_lote = stock_lote_db

        if instance.tipo == 'entrada':
            stock_disponible_operacion -= instance.cantidad
            if instance.lote and instance.lote == new_lote:
                 stock_disponible_lote -= instance.cantidad
        elif instance.tipo in ['salida', 'ajuste']:
            stock_disponible_operacion += instance.cantidad
            if instance.lote and instance.lote == new_lote:
                 stock_disponible_lote += instance.cantidad

        # 3. Ahora validamos si la *nueva* operación es posible con ese stock.
        if new_tipo in ['salida', 'ajuste']:
            if new_cantidad > stock_disponible_operacion:
                raise serializers.ValidationError({
                    'cantidad': f"Stock insuficiente para modificar '{producto.nombre}' (ID: {producto.id}). Disponible real: {stock_disponible_operacion}. Intentas asignar: {new_cantidad}."
                })
            if new_lote and new_cantidad > stock_disponible_lote:
                 raise serializers.ValidationError({
                    'cantidad': f"Stock insuficiente en lote '{new_lote.numero_lote}'. Disponible real: {stock_disponible_lote}. Intentas asignar: {new_cantidad}."
                })
        
        # Si la validación es exitosa, procedemos con la actualización normal.
        return super().update(instance, validated_data)