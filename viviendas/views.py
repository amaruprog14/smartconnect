from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from config.mixins import EliminacionProtegidaMixin
from config.permissions import (
    ParticipacionPermission, ViviendaPermission, exigir_administracion_terreno, filtrar_viviendas,
)
from .models import Vivienda
from .serializers import ParticipacionViviendaSerializer, ViviendaSerializer

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
        if self.action != 'list':
            return queryset
        queryset = filtrar_viviendas(queryset, self.request.user)
        # Filtros opcionales, aplicados sobre lo que el usuario ya puede ver:
        # ?terreno=<id> y ?identificador=<texto> (coincidencia exacta).
        terreno = self.request.query_params.get('terreno')
        if terreno is not None:
            if not terreno.isdigit():
                raise ValidationError({'terreno': 'Debe ser el id numérico de un terreno.'})
            queryset = queryset.filter(terreno_id=int(terreno))
        identificador = self.request.query_params.get('identificador')
        if identificador is not None:
            queryset = queryset.filter(identificador=identificador)
        return queryset

    def perform_create(self, serializer):
        exigir_administracion_terreno(self.request.user, serializer.validated_data['terreno'])
        serializer.save()

    def perform_update(self, serializer):
        terreno = serializer.validated_data.get('terreno', serializer.instance.terreno)
        exigir_administracion_terreno(self.request.user, terreno)
        serializer.save()

    @action(
        detail=True,
        methods=['get', 'post'],
        permission_classes=[IsAuthenticated, ParticipacionPermission],
        serializer_class=ParticipacionViviendaSerializer,
    )
    def participaciones(self, request, pk=None):
        """Operación del negocio: listar o asignar personas a esta vivienda.

        Orden de las reglas: get_object() aplica ParticipacionPermission (403 sin
        autoridad), luego el serializer valida datos y duplicados (400) y solo
        entonces se guarda. Ningún rechazo modifica la BD.
        """
        vivienda = self.get_object()
        if request.method == 'GET':
            participaciones = vivienda.participaciones.select_related('persona')
            return Response(self.get_serializer(participaciones, many=True).data)
        serializer = ParticipacionViviendaSerializer(
            data=request.data, context={**self.get_serializer_context(), 'vivienda': vivienda},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(vivienda=vivienda)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
