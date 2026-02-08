# apps/notificaciones/tests/test_notificaciones.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from ..productos.models import Producto, Categoria, Laboratorio
from ..usuario.models import Usuario
from ..notificaciones.models import NotificacionBajoStock
from apps.task.models import MovimientoInventario  # Ajusta si tu app se llama diferente


class NotificacionesTestCase(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username='admin_test', password='123', email='admin@test.com', rol='admin'
        )
        cat = Categoria.objects.create(nombre="Test")
        lab = Laboratorio.objects.create(nombre="TestLab")
        
        self.producto = Producto.objects.create(
            codigo="TEST001",
            nombre="Producto Test",
            categoria=cat,
            laboratorio=lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=10,
            stock_actual=15,  # Empieza con stock normal
            creado_por=self.admin
        )

    def test_notificacion_se_crea_automaticamente_al_bajar_stock(self):
        # Limpiar notificaciones
        NotificacionBajoStock.objects.all().delete()

        # Hacer una salida que baje el stock por debajo del mínimo
        MovimientoInventario.objects.create(
            producto=self.producto,
            tipo="salida",
            cantidad=10,  # 15 - 10 = 5 < 10 → bajo stock
            usuario=self.admin,
            motivo="Prueba"
        )

        # El signal crea la notificación

        self.assertTrue(
            NotificacionBajoStock.objects.filter(producto=self.producto).exists()
        )

    def test_no_se_crea_duplicado_en_24h(self):
        # Limpiar todo
        NotificacionBajoStock.objects.all().delete()

        # Primera notificación: se crea por movimiento
        MovimientoInventario.objects.create(
            producto=self.producto,
            tipo="salida",
            cantidad=5,  # 15 → 10 → 5
            usuario=self.admin
        )

        count_antes = NotificacionBajoStock.objects.filter(producto=self.producto).count()
        self.assertEqual(count_antes, 1)  # Debe haber 1

        # Segunda salida → debería disparar signal pero NO crear otra notificación
        MovimientoInventario.objects.create(
            producto=self.producto,
            tipo="salida",
            cantidad=2,
            usuario=self.admin
        )

        count_despues = NotificacionBajoStock.objects.filter(producto=self.producto).count()
        self.assertEqual(count_despues, 1)  # Sigue siendo 1