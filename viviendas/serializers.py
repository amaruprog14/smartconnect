from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Vivienda

class ViviendaSerializer(serializers.ModelSerializer):
    terreno_nombre = serializers.CharField(source='terreno.nombre', read_only=True)

    class Meta:
        model = Vivienda
        fields = ['id', 'terreno', 'terreno_nombre', 'identificador', 'tipo']
        read_only_fields = ['id', 'terreno_nombre']
        validators = [
            UniqueTogetherValidator(
                queryset=Vivienda.objects.all(),
                fields=['terreno', 'identificador'],
                message='Ya existe una vivienda con ese identificador en este terreno.',
            ),
        ]

    def validate_terreno(self, terreno):
        # Mover la vivienda dejaría a sus puntos de acceso en un terreno distinto.
        if self.instance and self.instance.terreno_id != terreno.pk and self.instance.puntos_acceso.exists():
            raise serializers.ValidationError(
                'No se puede cambiar el terreno de una vivienda que tiene puntos de acceso.'
            )
        return terreno
