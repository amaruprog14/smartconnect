from rest_framework import serializers
from .models import Persona

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'codigo', 'nombres', 'apellidos', 'email']
        read_only_fields = ['id']
