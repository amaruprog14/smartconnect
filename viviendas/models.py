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


class ParticipacionVivienda(models.Model):
    """Vínculo actual de una persona con una vivienda y su rol en ella.

    El rol vive aquí y no en Persona: alguien puede ser propietario en una
    vivienda y arrendatario en otra.
    """

    class Rol(models.TextChoices):
        PROPIETARIO_ADMIN = 'PROPIETARIO_ADMIN', 'Propietario administrador'
        PROPIETARIO = 'PROPIETARIO', 'Propietario'
        ARRENDATARIO = 'ARRENDATARIO', 'Arrendatario'
        CONVIVIENTE = 'CONVIVIENTE', 'Conviviente'

    # CASCADE: si se elimina la persona, sus vínculos actuales dejan de tener sentido.
    persona = models.ForeignKey('personas.Persona', on_delete=models.CASCADE, related_name='participaciones')
    # PROTECT: no se elimina una vivienda mientras tenga personas vinculadas.
    vivienda = models.ForeignKey(Vivienda, on_delete=models.PROTECT, related_name='participaciones')
    rol = models.CharField(max_length=20, choices=Rol.choices)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'participación en vivienda'
        verbose_name_plural = 'participaciones en viviendas'
        constraints = [
            models.UniqueConstraint(fields=['persona', 'vivienda'], name='participacion_unica_persona_vivienda'),
        ]

    def __str__(self):
        return f'{self.persona} - {self.get_rol_display()} en {self.vivienda}'
