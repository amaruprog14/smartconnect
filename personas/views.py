from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from config.permissions import PersonaPermission, filtrar_personas
from .models import Persona
from .serializers import PersonaSerializer

class PersonaViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = Persona.objects.order_by('id')
    serializer_class = PersonaSerializer
    permission_classes = [IsAuthenticated, PersonaPermission]
    # PROTECT impide dejar un terreno sin administrador por un borrado.
    mensaje_protegido = 'Esta persona administra terrenos. Reasigna sus terrenos antes de eliminarla.'

    def get_queryset(self):
        # Solo se filtra el listado. En detalle se busca entre todos para responder 403, no 404.
        queryset = super().get_queryset()
        return filtrar_personas(queryset, self.request.user) if self.action == 'list' else queryset
