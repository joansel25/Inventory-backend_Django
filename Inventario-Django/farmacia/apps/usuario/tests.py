
from rest_framework.test import APITestCase
from rest_framework import status
from apps.usuario.models import Usuario


class AuthTestCase(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@farmacia.com',
            rol='admin'
        )
        self.farmaceutico = Usuario.objects.create_user(
            username='farma1',
            password='farma123',
            email='farma@farmacia.com',
            rol='farmaceutico'
        )

    def test_login_jwt_correcto(self):
        """Prueba que el login devuelve tokens"""
        response = self.client.post('/api/token/', {
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_registro_por_admin(self):
        """Solo admin puede registrar nuevos usuarios"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/usuario/auth/usuarios/registro/', {
            'username': 'auxiliar1',
            'password': 'aux123',
            'first_name': 'Juan',
            'rol': 'auxiliar',
            'email': 'aux@farmacia.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.filter(username='auxiliar1').exists())

    def test_perfil_protegido(self):
        """El usuario autenticado puede ver su perfil"""
        self.client.force_authenticate(user=self.farmaceutico)
        response = self.client.get('/usuario/auth/usuarios/perfil/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'farma1')
        self.assertEqual(response.data['rol'], 'farmaceutico')