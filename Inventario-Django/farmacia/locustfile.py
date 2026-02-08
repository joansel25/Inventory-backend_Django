from locust import HttpUser, task, between
import random

class FarmaciaUser(HttpUser):
    wait_time = between(1, 3)  # Simula espera entre 1 y 5 segundos entre acciones
    token = None

    def on_start(self):
        """Se ejecuta al iniciar cada usuario simulado: Login para obtener Token"""
        response = self.client.post("/api/token/", json={
            "username": "admin_test",  # Asegúrate de que este usuario exista
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json()["access"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print("Login fallido en prueba de carga")

    @task(3)
    def listar_productos(self):
        """Simula ver el catálogo (acción frecuente)"""
        if self.token:
            self.client.get("/productos/", headers=self.headers)

    @task(1)
    def ver_dashboard_metrics(self):
        """Simula al admin revisando métricas"""
        if self.token:
            self.client.get("/monitoring/dashboard/", headers=self.headers)

    @task(2)
    def crear_movimiento(self):
        """Simula una operación de escritura (más pesada)"""
        if self.token:
            # Asumiendo que existe el producto con ID 1
            self.client.post("/task/movimientos/", json={
                "producto": 1,
                "tipo": "entrada",
                "cantidad": random.randint(1, 10),
                "motivo": "Prueba de carga automática"
            }, headers=self.headers)
