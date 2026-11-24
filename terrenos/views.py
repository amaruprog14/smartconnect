from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from config.permissions import TerrenoPermission, filtrar_terrenos
from .models import Terreno
from .serializers import TerrenoSerializer

class TerrenoViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = Terreno.objects.select_related('administrador').order_by('id')
    serializer_class = TerrenoSerializer
    permission_classes = [IsAuthenticated, TerrenoPermission]
    mensaje_protegido = (
        'Este terreno tiene viviendas o puntos de acceso. Elimínalos antes de eliminar el terreno.'
    )

    def get_queryset(self):
        # Solo se filtra el listado. En detalle se busca entre todos para responder 403, no 404.
        queryset = super().get_queryset()
        return filtrar_terrenos(queryset, self.request.user) if self.action == 'list' else queryset
