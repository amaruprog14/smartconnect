from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from config.permissions import ViviendaPermission, exigir_administracion_terreno, filtrar_viviendas
from .models import Vivienda
from .serializers import ViviendaSerializer

class ViviendaViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = Vivienda.objects.select_related('terreno').order_by('id')
    serializer_class = ViviendaSerializer
    permission_classes = [IsAuthenticated, ViviendaPermission]
    mensaje_protegido = (
        'Esta vivienda tiene puntos de acceso o participaciones. Elimínalos antes de eliminar la vivienda.'
    )

    def get_queryset(self):
        # Solo se filtra el listado. En detalle se busca entre todos para responder 403, no 404.
        queryset = super().get_queryset()
        return filtrar_viviendas(queryset, self.request.user) if self.action == 'list' else queryset

    def perform_create(self, serializer):
        exigir_administracion_terreno(self.request.user, serializer.validated_data['terreno'])
        serializer.save()

    def perform_update(self, serializer):
        terreno = serializer.validated_data.get('terreno', serializer.instance.terreno)
        exigir_administracion_terreno(self.request.user, terreno)
        serializer.save()
