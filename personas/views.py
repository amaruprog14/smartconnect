from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Persona
from .serializers import PersonaSerializer

class PersonaViewSet(ModelViewSet):
    queryset = Persona.objects.order_by('id')
    serializer_class = PersonaSerializer

    def destroy(self, request, *args, **kwargs):
        # PROTECT impide dejar un terreno sin administrador por un borrado.
        persona = self.get_object()
        try:
            self.perform_destroy(persona)
        except ProtectedError:
            return Response(
                {'detail': 'Esta persona administra terrenos. Reasigna sus terrenos antes de eliminarla.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
