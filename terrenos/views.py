from rest_framework.viewsets import ModelViewSet
from .models import Terreno
from .serializers import TerrenoSerializer

class TerrenoViewSet(ModelViewSet):
    queryset = Terreno.objects.select_related('administrador').order_by('id')
    serializer_class = TerrenoSerializer
