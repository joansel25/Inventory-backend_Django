import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'farmacia'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmacia.settings')
django.setup()

from apps.usuario.models import Usuario
from django.contrib.auth import authenticate

def run():
    print("--- Reproduciendo Creación de Usuarios ---")
    
    username = 'usuario_prueba_script'
    password = 'password_seguro_123'

    # 1. Crear usuario usando el Manager (forma correcta)
    print(f"\n1. Creando usuario '{username}' con create_user...")
    try:
        if Usuario.objects.filter(username=username).exists():
            Usuario.objects.get(username=username).delete()
            print("   (Usuario previo eliminado)")
        
        user = Usuario.objects.create_user(username=username, password=password, email='prueba@test.com')
        print(f"   Usuario creado. ID: {user.id}")
        print(f"   Password hasheado: {user.password}")
        if not user.password.startswith('pbkdf2_') and not user.password.startswith('argon2'):
             print("   [ALERTA] El password no parece estar hasheado estándar Django.")
    except Exception as e:
        print(f"   [ERROR] Falló create_user: {e}")
        return

    # 2. Probar autenticación
    print(f"\n2. Probando authenticate(username='{username}', password='{password}')...")
    user_auth = authenticate(username=username, password=password)
    if user_auth:
        print("   [ÉXITO] Usuario autenticado correctamente.")
    else:
        print("   [FALLO] Autenticación fallida.")

    # 3. Simular error común: Crear usuario como objeto normal sin set_password
    print("\n3. Simulando creación incorrecta (como podrida ocurrir en un script mal hecho)...")
    username_bad = 'usuario_mal_creado'
    try:
        if Usuario.objects.filter(username=username_bad).exists():
            Usuario.objects.get(username=username_bad).delete()
        
        # INCORRECTO: Asignar password directo
        user_bad = Usuario(username=username_bad, email='bad@test.com')
        user_bad.password = password 
        user_bad.save()
        print(f"   Usuario '{username_bad}' creado incorrectamente.")
        print(f"   Password almacenado (texto plano): {user_bad.password}")
        
        # Intentar autenticar
        user_auth_bad = authenticate(username=username_bad, password=password)
        if user_auth_bad:
             print("   [SORPRESA] Autenticó (no debería si Django espera hash).")
        else:
             print("   [ÉXITO] No autenticó (comportamiento esperado para password plano).")
             
    except Exception as e:
        print(f"   [ERROR] {e}")

if __name__ == '__main__':
    run()
