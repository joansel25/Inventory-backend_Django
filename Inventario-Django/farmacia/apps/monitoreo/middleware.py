import time
from .models import APIMetric

class PerformanceMonitoringMiddleware:
    """
    Middleware para medir latencia y registrar métricas de uso de la API.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Procesar la petición
        response = self.get_response(request)
        
        duration = (time.time() - start_time) * 1000  # Convertir a ms

        # Registrar solo peticiones a la API para no llenar la BD con estáticos o admin
        if request.path.startswith('/api/') or request.path.startswith('/task/') or request.path.startswith('/productos/'):
            # En un entorno de producción real, esto debería enviarse a una cola (Celery)
            # para no bloquear la respuesta, pero para este alcance es funcional.
            try:
                # Determinar usuario (DRF autentica antes de retornar la respuesta, así que request.user debería estar listo)
                user = request.user if request.user.is_authenticated else None
                
                # Determinar estado legible
                if 200 <= response.status_code < 300:
                    estado_txt = 'Exitoso'
                elif 400 <= response.status_code < 500:
                    estado_txt = 'Error Cliente'
                else:
                    estado_txt = 'Error Servidor'

                # Generar mensaje básico
                msg = f"Acción {request.method} en {request.path}"

                APIMetric.objects.create(
                    usuario=user,
                    endpoint=request.path,
                    metodo=request.method,
                    codigo_estado=response.status_code,
                    estado=estado_txt,
                    mensaje=msg,
                    tiempo_respuesta_ms=duration
                )
            except Exception:
                pass # Fallar silenciosamente para no afectar al usuario
                
        return response
