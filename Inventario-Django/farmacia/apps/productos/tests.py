# apps/productos/tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..productos.models import Categoria, Laboratorio, Producto
from ..usuario.models import Usuario


class ProductosTestCase(APITestCase):
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.admin = Usuario.objects.create_superuser(
            username='admin_test', 
            password='test123', 
            email='admin@test.com',
            rol='admin'
        )
        self.farma = Usuario.objects.create_user(
            username='farma_test', 
            password='test123', 
            email='farma@test.com',
            rol='farmaceutico'
        )
        self.auxiliar = Usuario.objects.create_user(
            username='aux_test',
            password='test123',
            email='aux@test.com',
            rol='auxiliar'
        )

        self.categoria = Categoria.objects.create(
            nombre="Analgésicos",
            descripcion="Medicamentos para el dolor"
        )
        self.lab = Laboratorio.objects.create(
            nombre="Genfar",
            pais="Colombia"
        )

        # URL base para productos
        self.base_url = reverse('producto-list')

    def test_crear_producto_genera_codigo_automatico(self):
        """Verifica que el código se genere automáticamente"""
        self.client.force_authenticate(user=self.farma)

        data = {
            # ⚠️ NO enviar 'codigo', se genera automáticamente
            "nombre": "Paracetamol 500mg",
            "categoria": self.categoria.id,
            "laboratorio": self.lab.id,
            "precio_compra": "800.00",
            "precio_venta": "1500.00",
            "stock_minimo": 20
        }

        response = self.client.post(self.base_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Producto.objects.count(), 1)
        
        producto = Producto.objects.first()
        self.assertTrue(producto.codigo.startswith("PROD-"))
        self.assertEqual(producto.creado_por, self.farma)

    def test_listar_productos_autenticado(self):
        """Lista productos con usuario autenticado"""
        Producto.objects.create(
            nombre="Producto List Test",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=5,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_listar_productos_sin_autenticar_falla(self):
        """Verifica que se requiere autenticación"""
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detalle_producto(self):
        """Obtiene el detalle de un producto específico"""
        producto = Producto.objects.create(
            nombre="Detalle Test",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=5,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.admin)
        url = reverse('producto-detail', kwargs={'pk': producto.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Detalle Test")
        self.assertTrue(response.data["codigo"].startswith("PROD-"))

    def test_actualizar_producto_como_farmaceutico(self):
        """Farmacéutico puede actualizar productos"""
        producto = Producto.objects.create(
            nombre="Producto viejo",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=5,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.farma)
        url = reverse('producto-detail', kwargs={'pk': producto.id})
        data = {"nombre": "Producto actualizado"}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Producto actualizado")

    def test_auxiliar_no_puede_crear_producto(self):
        """Auxiliar NO tiene permiso para crear productos"""
        self.client.force_authenticate(user=self.auxiliar)

        data = {
            "nombre": "Test Auxiliar",
            "categoria": self.categoria.id,
            "laboratorio": self.lab.id,
            "precio_compra": "1000.00",
            "precio_venta": "2000.00",
            "stock_minimo": 10
        }

        response = self.client.post(self.base_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_auxiliar_puede_listar_productos(self):
        """Auxiliar puede ver la lista de productos (solo lectura)"""
        Producto.objects.create(
            nombre="Producto Visible",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=5,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.auxiliar)
        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_eliminar_producto_como_admin(self):
        """Admin puede eliminar productos"""
        producto = Producto.objects.create(
            nombre="Producto a eliminar",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=5,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.admin)
        url = reverse('producto-detail', kwargs={'pk': producto.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Producto.objects.count(), 0)

    def test_eliminar_producto_como_farmaceutico(self):
        """Farmacéutico puede eliminar productos"""
        producto = Producto.objects.create(
            nombre="Producto a eliminar Farma",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=5,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.farma)
        url = reverse('producto-detail', kwargs={'pk': producto.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Producto.objects.count(), 0)

    def test_bajo_stock_property_funciona(self):
        """Verifica que la property bajo_stock funciona correctamente"""
        producto = Producto.objects.create(
            nombre="Producto Bajo Stock",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_minimo=10,
            stock_actual=5,  # Menor que stock_minimo
            creado_por=self.admin
        )
        
        # ⚠️ CORRECCIÓN: bajo_stock es @property, NO se llama con ()
        self.assertTrue(producto.bajo_stock)  # SIN paréntesis

    def test_ganancia_porcentual_calculada(self):
        """Verifica el cálculo de ganancia porcentual"""
        producto = Producto.objects.create(
            nombre="Test Ganancia",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=1500,
            stock_minimo=5,
            creado_por=self.admin
        )
        
        # Ganancia = ((1500-1000)/1000) * 100 = 50%
        self.assertEqual(producto.ganancia_porcentual, 50.0)

    def test_endpoint_bajo_stock(self):
        """Verifica que el endpoint /bajo_stock/ funciona"""
        Producto.objects.create(
            nombre="Producto Bajo Stock",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1000,
            precio_venta=2000,
            stock_actual=3,
            stock_minimo=10,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.admin)
        url = reverse('producto-bajo-stock')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_pdf_individual_producto(self):
        """Verifica generación de PDF individual"""
        producto = Producto.objects.create(
            nombre="Ibuprofeno 400mg",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1200,
            precio_venta=2200,
            stock_minimo=15,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.farma)
        url = reverse('producto-pdf', kwargs={'pk': producto.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')

    def test_pdf_catalogo_completo(self):
        """Verifica generación de PDF de catálogo"""
        Producto.objects.create(
            nombre="Producto PDF",
            categoria=self.categoria,
            laboratorio=self.lab,
            precio_compra=1200,
            precio_venta=2200,
            stock_minimo=15,
            creado_por=self.admin
        )

        self.client.force_authenticate(user=self.admin)
        url = reverse('producto-todos-pdf')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')