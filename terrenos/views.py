from rest_framework.exceptions import PermissionDenied
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

    def perform_update(self, serializer):
        # El administrador edita nombre, código y dirección, pero no puede ceder el terreno:
        # cambiar quién lo administra es una decisión del staff. Repetir el actual se permite.
        nuevo = serializer.validated_data.get('administrador')
        if (not self.request.user.is_staff and nuevo is not None
                and nuevo.pk != serializer.instance.administrador_id):
            raise PermissionDenied('Solo el personal (staff) puede cambiar el administrador de un terreno.')
        serializer.save()
