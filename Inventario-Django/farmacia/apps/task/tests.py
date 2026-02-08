# apps/task/tests/test_movimientos.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..usuario.models import Usuario
from ..productos.models import Categoria, Laboratorio, Producto
from apps.task.models import MovimientoInventario


class MovimientosTestCase(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username='admin_test', email='admin@test.com', password='admin123', rol='admin'
        )
        self.farmaceutico = Usuario.objects.create_user(
            username='farma_test', password='123', email='farma@test.com', rol='farmaceutico'
        )
        self.auxiliar = Usuario.objects.create_user(
            username='aux_test', password='123', email='aux@test.com', rol='auxiliar'
        )

        self.categoria = Categoria.objects.create(nombre="Analgésicos")
        self.laboratorio = Laboratorio.objects.create(nombre="Genfar")

        self.producto = Producto.objects.create(
            codigo="PARA001",
            nombre="Paracetamol 500mg",
            categoria=self.categoria,
            laboratorio=self.laboratorio,
            precio_compra=800.00,
            precio_venta=1500.00,
            stock_minimo=10,
            stock_actual=0,
            creado_por=self.admin
        )

        self.list_url = reverse('movimiento-list')
        self.pdf_all_url = reverse('movimiento-todos-pdf')

    def test_entrada_aumenta_stock(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "entrada",
            "cantidad": 100,
            "motivo": "Compra inicial"  # obligatorio ahora
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 100)

    def test_salida_no_permite_sin_stock(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "salida",
            "cantidad": 50,
            "motivo": "Intento sin stock"  # obligatorio
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # El mensaje cambió, ahora es más claro
        self.assertIn("Stock insuficiente", str(response.data))

    def test_salida_valida_resta_stock(self):
        self.client.force_authenticate(user=self.admin)
        
        # Entrada primero
        self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "entrada",
            "cantidad": 80,
            "motivo": "Carga inicial"
        }, format='json')

        # Salida válida
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "salida",
            "cantidad": 30,
            "motivo": "Venta"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 50)

    def test_auxiliar_no_puede_crear_movimiento(self):
        self.client.force_authenticate(user=self.auxiliar)
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "entrada",
            "cantidad": 10,
            "motivo": "Prueba rol"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_farmaceutico_puede_crear_movimiento(self):
        self.client.force_authenticate(user=self.farmaceutico)
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "entrada",
            "cantidad": 25,
            "motivo": "Reposición"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_farmaceutico_puede_editar_y_eliminar_movimiento(self):
        """Verifica que el farmacéutico tenga CRUD completo en movimientos"""
        self.client.force_authenticate(user=self.farmaceutico)
        
        # 1. Crear
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "entrada",
            "cantidad": 10,
            "motivo": "Test CRUD Farma"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mov_id = response.data['id']

        # 2. Editar
        url_detail = reverse('movimiento-detail', kwargs={'pk': mov_id})
        response = self.client.patch(url_detail, {"motivo": "Editado por Farma"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['motivo'], "Editado por Farma")

        # 3. Eliminar
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_pdf_todos_los_movimientos(self):
        self.client.force_authenticate(user=self.admin)
        MovimientoInventario.objects.create(
            producto=self.producto, tipo="entrada", cantidad=100, usuario=self.admin, motivo="Test PDF"
        )
        response = self.client.get(self.pdf_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')

    def test_crud_completo(self):
        self.client.force_authenticate(user=self.admin)

        # CREATE
        response = self.client.post(self.list_url, {
            "producto": self.producto.id,
            "tipo": "entrada",
            "cantidad": 60,
            "motivo": "CRUD test"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mov_id = response.data['id']

        # READ
        response = self.client.get(reverse('movimiento-detail', kwargs={'pk': mov_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # UPDATE
        response = self.client.patch(
            reverse('movimiento-detail', kwargs={'pk': mov_id}),
            {"motivo": "Actualizado"}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # DELETE
        response = self.client.delete(reverse('movimiento-detail', kwargs={'pk': mov_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)