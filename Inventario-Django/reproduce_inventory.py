import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'farmacia'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmacia.settings')
django.setup()

from apps.productos.models import Producto, Categoria, Laboratorio, PrincipioActivo
from apps.task.models import MovimientoInventario
from apps.usuario.models import Usuario
from django.core.exceptions import ValidationError

def run():
    print("--- Reproduciendo Lógica de Inventario ---")

    # 1. Crear datos de prueba
    print("1. Creando datos de prueba...")
    try:
        user, _ = Usuario.objects.get_or_create(username='test_user', defaults={'email': 'test@example.com'})
        cat, _ = Categoria.objects.get_or_create(nombre='Test Categoria')
        lab, _ = Laboratorio.objects.get_or_create(nombre='Test Lab')
        principio, _ = PrincipioActivo.objects.get_or_create(nombre='Test Principio')
        
        # Limpiar producto de prueba anterior si existe
        Producto.objects.filter(nombre='Producto Test Stock').delete()
        
        producto = Producto.objects.create(
            nombre='Producto Test Stock',
            categoria=cat,
            laboratorio=lab,
            principio_activo=principio,
            precio_compra=100,
            precio_venta=150,
            creado_por=user
        )
        print(f"   Producto creado: {producto} - Stock Inicial: {producto.stock_actual}")
    except Exception as e:
        print(f"ERROR creando datos: {e}")
        return

    # 2. Intentar Salida sin stock (Debe fallar)
    print("\n2. Intentando SALIDA sin stock (Debería fallar)...")
    try:
        mov = MovimientoInventario(
            producto=producto,
            tipo='salida',
            cantidad=5,
            motivo='Prueba salida sin stock',
            usuario=user
        )
        mov.full_clean() # Valida con clean() del modelo
        mov.save()
        print("   [FALLO] Se permitió salida sin stock!")
    except ValidationError as e:
        print(f"   [ÉXITO] Validación correcta: {e}")
    except Exception as e:
        print(f"   [ERROR] Excepción inesperada: {e}")

    # 3. Realizar Entrada
    print("\n3. Realizando ENTRADA de 10 unidades...")
    try:
        mov_entrada = MovimientoInventario.objects.create(
            producto=producto,
            tipo='entrada',
            cantidad=10,
            motivo='Prueba entrada',
            usuario=user
        )
        producto.refresh_from_db()
        print(f"   Entrada creada. Nuevo Stock: {producto.stock_actual} (Esperado: 10)")
        if producto.stock_actual != 10:
             print("   [FALLO] El stock no se actualizó correctamente.")
    except Exception as e:
        print(f"   [ERROR] Fallo en entrada: {e}")

    # 4. Realizar Salida Válida
    print("\n4. Realizando SALIDA válida de 3 unidades...")
    try:
        mov_salida = MovimientoInventario(
            producto=producto,
            tipo='salida',
            cantidad=3,
            motivo='Prueba salida valida',
            usuario=user
        )
        mov_salida.full_clean()
        mov_salida.save()
        producto.refresh_from_db()
        print(f"   Salida creada. Nuevo Stock: {producto.stock_actual} (Esperado: 7)")
        if producto.stock_actual != 7:
             print("   [FALLO] El stock no se actualizó correctamente tras salida.")
    except Exception as e:
        print(f"   [ERROR] Fallo en salida válida: {e}")

    # 5. Modificar Salida (Caso complejo: validar stock disponible al editar)
    print("\n5. Editando SALIDA anterior (de 3 a 12 unidades) - Debe fallar pues stock (7+3=10) < 12...")
    # Stock actual: 7. Si devuelvo los 3, tendría 10. Si intento sacar 12, no alcanza.
    try:
        mov_salida.cantidad = 12
        mov_salida.full_clean()
        mov_salida.save()
        print("   [FALLO] Se permitió modificar salida a cantidad excedente!")
    except ValidationError as e:
        print(f"   [ÉXITO] Validación correcta al editar: {e}")
    except Exception as e:
        # Nota: El metodo save() personalizado maneja la logica, full_clean() llama a clean()
        # Si la validación está en save(), full_clean podría pasar pero save fallar.
        print(f"   [INFO] Excepción en save/validación: {e}")

    # 6. Check final
    producto.refresh_from_db()
    print(f"\nStock Final en DB: {producto.stock_actual}")

if __name__ == '__main__':
    run()
