from django.db import models

class Vivienda(models.Model):
    class Tipo(models.TextChoices):
        CASA = 'CASA', 'Casa'
        DEPARTAMENTO = 'DEPARTAMENTO', 'Departamento'

    terreno = models.ForeignKey('terrenos.Terreno', on_delete=models.PROTECT, related_name='viviendas')
    # Nombre visible dentro del terreno, por ejemplo "Casa 1" o "Depto 201".
    identificador = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)

    class Meta:
        ordering = ['id']
        constraints = [
            # Dos terrenos pueden tener una "Casa 1"; dentro del mismo terreno no se repite.
            models.UniqueConstraint(fields=['terreno', 'identificador'], name='vivienda_unica_por_terreno'),
        ]

    def __str__(self):
        return f'{self.identificador} ({self.terreno})'
