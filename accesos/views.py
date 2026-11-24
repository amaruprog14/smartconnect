from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from .models import PuntoAcceso
from .serializers import PuntoAccesoSerializer

class PuntoAccesoViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = PuntoAcceso.objects.select_related('terreno').order_by('id')
    serializer_class = PuntoAccesoSerializer
