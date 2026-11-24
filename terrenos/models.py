from django.db import models

class Terreno(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    administrador = models.ForeignKey(
        'personas.Persona',
        on_delete=models.PROTECT,
        related_name='terrenos_administrados',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.nombre
