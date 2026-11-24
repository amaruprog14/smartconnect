from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from .models import Persona
from .serializers import PersonaSerializer

class PersonaViewSet(EliminacionProtegidaMixin, ModelViewSet):
    queryset = Persona.objects.order_by('id')
    serializer_class = PersonaSerializer
    # PROTECT impide dejar un terreno sin administrador por un borrado.
    mensaje_protegido = 'Esta persona administra terrenos. Reasigna sus terrenos antes de eliminarla.'
