from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from config.permissions import PuntoAccesoPermission, exigir_administracion_terreno, filtrar_puntos_acceso
from .models import PuntoAcceso
from .serializers import PuntoAccesoSerializer

class PuntoAccesoViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = PuntoAcceso.objects.select_related('terreno').order_by('id')
    serializer_class = PuntoAccesoSerializer
    permission_classes = [IsAuthenticated, PuntoAccesoPermission]

    def get_queryset(self):
        # Solo se filtra el listado. En detalle se busca entre todos para responder 403, no 404.
        queryset = super().get_queryset()
        return filtrar_puntos_acceso(queryset, self.request.user) if self.action == 'list' else queryset

    def perform_create(self, serializer):
        exigir_administracion_terreno(self.request.user, serializer.validated_data['terreno'])
        serializer.save()

    def perform_update(self, serializer):
        terreno = serializer.validated_data.get('terreno', serializer.instance.terreno)
        exigir_administracion_terreno(self.request.user, terreno)
        serializer.save()
