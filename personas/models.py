from django.db import models

class Persona(models.Model):
    # Identificador ficticio de la práctica. No pretende validar un RUT.
    codigo = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'
