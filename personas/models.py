from django.conf import settings
from django.db import models

class Persona(models.Model):
    # Identificador ficticio de la práctica. No pretende validar un RUT.
    codigo = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    # Cuenta con la que esta persona inicia sesión. Es opcional: no todas las
    # personas del dominio usan la API, y una cuenta representa a una sola persona.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='persona',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'
