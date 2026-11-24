from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from .models import Terreno
from .serializers import TerrenoSerializer

class TerrenoViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = Terreno.objects.select_related('administrador').order_by('id')
    serializer_class = TerrenoSerializer
    mensaje_protegido = (
        'Este terreno tiene viviendas o puntos de acceso. Elimínalos antes de eliminar el terreno.'
    )
