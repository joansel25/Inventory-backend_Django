# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('farmaceutico', 'Farmacéutico'),
        ('bodeguero', 'Bodeguero'),
        ('auxiliar', 'Auxiliar de Farmacia'),
    )

    rol = models.CharField(max_length=20, choices=ROLES, default='auxiliar')
    telefono = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"