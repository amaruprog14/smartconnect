from django.db.models import Exists, OuterRef
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from config.mixins import Conflicto, EliminacionProtegidaMixin
from config.permissions import PersonaPermission, filtrar_personas
from viviendas.models import ParticipacionVivienda
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

    def perform_destroy(self, persona):
        # Las participaciones se borran en CASCADE con la persona, pero ninguna vivienda debe
        # quedar sin propietario administrador activo: solo él (o el staff) gestiona a sus personas.
        PA = ParticipacionVivienda.Rol.PROPIETARIO_ADMIN
        otro_admin = ParticipacionVivienda.objects.filter(
            vivienda=OuterRef('vivienda'), rol=PA, activa=True,
        ).exclude(persona=persona)
        unicas = persona.participaciones.filter(rol=PA, activa=True).filter(~Exists(otro_admin))
        viviendas = [str(p.vivienda) for p in unicas.select_related('vivienda__terreno')]
        if viviendas:
            raise Conflicto(
                'Esta persona es el único PROPIETARIO_ADMIN activo de: ' + ', '.join(viviendas)
                + '. Asigna otro propietario administrador antes de eliminarla.'
            )
        super().perform_destroy(persona)
