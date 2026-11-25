from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import ParticipacionVivienda, Vivienda

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


class ParticipacionViviendaSerializer(serializers.ModelSerializer):
    """Asignación de una persona a la vivienda indicada en la URL.

    La vivienda llega por contexto desde la vista; el cliente envía persona y rol.
    """
    persona_nombre = serializers.CharField(source='persona.__str__', read_only=True)

    class Meta:
        model = ParticipacionVivienda
        fields = ['id', 'persona', 'persona_nombre', 'vivienda', 'rol', 'activa']
        read_only_fields = ['id', 'persona_nombre', 'vivienda', 'activa']

    def validate(self, attrs):
        # Se valida aquí, antes de guardar, para responder 400 sin depender del IntegrityError.
        vivienda = self.context['vivienda']
        if ParticipacionVivienda.objects.filter(persona=attrs['persona'], vivienda=vivienda).exists():
            raise serializers.ValidationError(
                {'persona': 'Esta persona ya tiene una participación en esta vivienda.'}
            )
        return attrs
