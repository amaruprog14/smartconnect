from django.core.exceptions import ValidationError
from django.db import models

class PuntoAcceso(models.Model):
    class Tipo(models.TextChoices):
        PUERTA = 'PUERTA', 'Puerta'
        PORTON = 'PORTON', 'Portón'

    terreno = models.ForeignKey('terrenos.Terreno', on_delete=models.PROTECT, related_name='puntos_acceso')
    # Vacía para accesos comunes del terreno; con valor para el acceso privado de una vivienda.
    vivienda = models.ForeignKey(
        'viviendas.Vivienda', on_delete=models.PROTECT, null=True, blank=True, related_name='puntos_acceso',
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'punto de acceso'
        verbose_name_plural = 'puntos de acceso'

    def clean(self):
        # Misma regla que el serializer, para que el admin tampoco la salte.
        if self.vivienda_id and self.terreno_id and self.vivienda.terreno_id != self.terreno_id:
            raise ValidationError({'vivienda': 'La vivienda debe pertenecer al mismo terreno del punto de acceso.'})

    def __str__(self):
        return f'{self.nombre} ({self.terreno})'
