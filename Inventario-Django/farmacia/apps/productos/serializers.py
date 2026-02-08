# apps/productos/serializers.py
from rest_framework import serializers
from .models import Categoria, PrincipioActivo, Laboratorio, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    productos_count = serializers.IntegerField(source='productos.count', read_only=True)

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'activo', 'fecha_creacion', 'productos_count']
        read_only_fields = ['fecha_creacion']


class PrincipioActivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrincipioActivo
        fields = '__all__'


class LaboratorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorio
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    # ✅ CORRECCIÓN: Sin source='bajo_stock' porque es redundante
    bajo_stock = serializers.BooleanField(read_only=True)
    
    # ✅ CORRECCIÓN: Sin source='estado_stock' porque es redundante
    estado_stock = serializers.CharField(read_only=True)
    
    ganancia_porcentual = serializers.SerializerMethodField()
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    laboratorio_nombre = serializers.CharField(source='laboratorio.nombre', read_only=True)
    principio_activo_nombre = serializers.CharField(source='principio_activo.nombre', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.get_full_name', read_only=True, default='Sistema')

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'categoria', 'categoria_nombre',
            'principio_activo', 'principio_activo_nombre', 'laboratorio', 'laboratorio_nombre',
            'precio_compra', 'precio_venta', 'ganancia_porcentual',
            'stock_minimo', 'stock_actual', 'bajo_stock', 'estado_stock',
            'imagen', 'activo', 'fecha_creacion', 'creado_por', 'creado_por_nombre'
        ]
        read_only_fields = [
            'codigo', 'stock_actual', 'fecha_creacion', 'creado_por', 
            'creado_por_nombre', 'ganancia_porcentual', 'bajo_stock', 'estado_stock'
        ]

    def get_ganancia_porcentual(self, obj):
        """Obtiene la ganancia porcentual del producto (es una @property)"""
        return obj.ganancia_porcentual  # ✅ Sin paréntesis porque es @property