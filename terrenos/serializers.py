from rest_framework import serializers
from .models import Terreno

class TerrenoSerializer(serializers.ModelSerializer):
    administrador_nombre = serializers.CharField(source='administrador.__str__', read_only=True)

    class Meta:
        model = Terreno
        fields = ['id', 'codigo', 'nombre', 'direccion', 'administrador', 'administrador_nombre']
        read_only_fields = ['id', 'administrador_nombre']
