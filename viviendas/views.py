from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from .models import Vivienda
from .serializers import ViviendaSerializer

class ViviendaViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = Vivienda.objects.select_related('terreno').order_by('id')
    serializer_class = ViviendaSerializer
    mensaje_protegido = (
        'Esta vivienda tiene puntos de acceso o participaciones. Elimínalos antes de eliminar la vivienda.'
    )
