from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
from django.db import IntegrityError

def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado para capturar ProtectedError (Integridad de BD)
    y devolver un mensaje amigable al frontend en lugar de un error 500.
    """
    # Llama al manejador por defecto de DRF primero
    response = exception_handler(exc, context)

    # Si DRF no manejó la excepción (response es None) y es un ProtectedError
    if response is None and isinstance(exc, ProtectedError):
        return Response(
            {"error": "No se puede eliminar este registro porque tiene movimientos o datos asociados. Elimine primero los registros dependientes o desactive el producto."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Capturar errores de integridad (como Stock Negativo)
    if response is None and isinstance(exc, IntegrityError):
        if 'stock_actual_check' in str(exc):
            return Response(
                {"error": "Operación rechazada: El stock resultante sería negativo. Verifique la cantidad o el tipo de movimiento."},
                status=status.HTTP_400_BAD_REQUEST
            )

    return response