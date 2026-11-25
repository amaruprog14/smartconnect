from rest_framework import serializers
from .models import PuntoAcceso

class PuntoAccesoSerializer(serializers.ModelSerializer):
    terreno_nombre = serializers.CharField(source='terreno.nombre', read_only=True)

    class Meta:
        model = PuntoAcceso
        fields = ['id', 'terreno', 'terreno_nombre', 'vivienda', 'nombre', 'tipo', 'activo']
        read_only_fields = ['id', 'terreno_nombre']

    def validate(self, attrs):
        # En PATCH puede venir solo uno de los dos campos: se completa con el valor guardado.
        terreno = attrs.get('terreno', getattr(self.instance, 'terreno', None))
        vivienda = attrs.get('vivienda', getattr(self.instance, 'vivienda', None))
        if vivienda is not None and terreno is not None and vivienda.terreno_id != terreno.pk:
            raise serializers.ValidationError(
                {'vivienda': 'La vivienda debe pertenecer al mismo terreno del punto de acceso.'}
            )
        return attrs
