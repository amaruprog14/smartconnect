from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response


class Conflicto(APIException):
    """409 para reglas de borrado que on_delete no expresa por sí solo."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'El registro no se puede eliminar en su estado actual.'
    default_code = 'conflicto'


class EliminacionProtegidaMixin:
    """Responde 409 cuando on_delete=PROTECT impide eliminar el registro.

    Cada ViewSet define `mensaje_protegido` explicando qué hay que reasignar o
    eliminar antes. Así el cliente recibe un motivo claro en vez de un error 500.
    """
    mensaje_protegido = 'El registro tiene datos relacionados y no se puede eliminar.'

    def destroy(self, request, *args, **kwargs):
        instancia = self.get_object()
        try:
            self.perform_destroy(instancia)
        except ProtectedError:
            return Response({'detail': self.mensaje_protegido}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)
