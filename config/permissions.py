"""Permisos por alcance de SmartConnect.

JWT solo identifica la cuenta (request.user). Estas clases deciden qué puede
hacer esa cuenta según su vínculo con el terreno o la vivienda:

- is_staff: acceso completo a los cuatro maestros.
- Administrador de un terreno: edita ese terreno y gestiona sus viviendas y
  puntos de acceso.
- Persona con participación activa en una vivienda: ve esa vivienda y su terreno.
- Asignar personas a una vivienda (ver ParticipacionPermission): el staff
  asigna cualquier rol en cualquier vivienda; el propietario administrador
  activo de ESA vivienda asigna los roles no administradores. Administrar el
  terreno no da esa autoridad.

Los listados se filtran con las funciones filtrar_* desde get_queryset. En
detalle, edición y borrado el ViewSet busca entre todos los registros y
has_object_permission responde 403 si el objeto está fuera del alcance, en vez
de un 404 que ocultaría el motivo.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission
from viviendas.models import ParticipacionVivienda

SIN_PERSONA = 'Tu cuenta no está vinculada a una persona.'
PROPIETARIO_ADMIN = ParticipacionVivienda.Rol.PROPIETARIO_ADMIN


def persona_de(user):
    """Persona vinculada a la cuenta, o None si no tiene."""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.persona
    except ObjectDoesNotExist:
        return None


def participa(persona, vivienda, rol=None):
    """True si la persona tiene una participación activa en la vivienda (con ese rol, si se indica)."""
    if persona is None:
        return False
    participaciones = vivienda.participaciones.filter(persona=persona, activa=True)
    if rol is not None:
        participaciones = participaciones.filter(rol=rol)
    return participaciones.exists()


# ---------------------------------------------------------------- listados

def filtrar_personas(queryset, user):
    return queryset if user.is_staff else queryset.filter(usuario=user)


def filtrar_terrenos(queryset, user):
    """Terrenos que administra o donde tiene una vivienda."""
    if user.is_staff:
        return queryset
    persona = persona_de(user)
    if persona is None:
        return queryset.none()
    return queryset.filter(
        Q(administrador=persona)
        | Q(viviendas__participaciones__persona=persona, viviendas__participaciones__activa=True)
    ).distinct()


def filtrar_viviendas(queryset, user):
    """Viviendas de los terrenos que administra y aquellas donde participa."""
    if user.is_staff:
        return queryset
    persona = persona_de(user)
    if persona is None:
        return queryset.none()
    return queryset.filter(
        Q(terreno__administrador=persona)
        | Q(participaciones__persona=persona, participaciones__activa=True)
    ).distinct()


def filtrar_puntos_acceso(queryset, user):
    """Puntos de acceso de los terrenos que administra."""
    if user.is_staff:
        return queryset
    persona = persona_de(user)
    if persona is None:
        return queryset.none()
    return queryset.filter(terreno__administrador=persona)


def exigir_administracion_terreno(user, terreno):
    """Antes de guardar una vivienda o un punto: el terreno destino debe ser del solicitante."""
    if user.is_staff:
        return
    persona = persona_de(user)
    if persona is None or terreno.administrador_id != persona.pk:
        raise PermissionDenied('Solo el administrador de ese terreno puede registrar o mover datos en él.')


# ---------------------------------------------------------------- maestros

class PersonaPermission(BasePermission):
    """Staff: todo. Usuario normal: ve y edita solo su propia persona."""

    def has_permission(self, request, view):
        if request.user.is_staff or view.action not in ('create', 'destroy'):
            return True
        self.message = 'Solo el personal (staff) puede crear o eliminar personas.'
        return False

    def has_object_permission(self, request, view, persona):
        if request.user.is_staff or persona.usuario_id == request.user.pk:
            return True
        self.message = 'Solo puedes ver o editar tu propia persona.'
        return False


class TerrenoPermission(BasePermission):
    """Ver: administrador o residente. Editar: administrador. Crear o eliminar: staff."""

    def has_permission(self, request, view):
        if request.user.is_staff or view.action not in ('create', 'destroy'):
            return True
        self.message = 'Solo el personal (staff) puede crear o eliminar terrenos.'
        return False

    def has_object_permission(self, request, view, terreno):
        if request.user.is_staff:
            return True
        persona = persona_de(request.user)
        if persona is None:
            self.message = SIN_PERSONA
            return False
        if terreno.administrador_id == persona.pk:
            return True
        if request.method in SAFE_METHODS:
            if ParticipacionVivienda.objects.filter(persona=persona, activa=True, vivienda__terreno=terreno).exists():
                return True
            self.message = 'Este terreno está fuera de tu alcance.'
            return False
        self.message = 'Solo el administrador de este terreno puede modificarlo.'
        return False


class AlcanceTerrenoPermission(BasePermission):
    """Base para viviendas y puntos de acceso: los gestiona el administrador de su terreno."""

    def has_permission(self, request, view):
        if request.user.is_staff or request.method in SAFE_METHODS:
            return True
        persona = persona_de(request.user)
        if persona is None:
            self.message = SIN_PERSONA
            return False
        if view.action == 'create' and not persona.terrenos_administrados.exists():
            self.message = 'Solo el administrador de un terreno puede crear registros en él.'
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        persona = persona_de(request.user)
        if persona is not None and obj.terreno.administrador_id == persona.pk:
            return True
        if request.method in SAFE_METHODS:
            if self.puede_ver(persona, obj):
                return True
            self.message = 'Este registro está fuera de tu alcance.'
            return False
        self.message = 'Solo el administrador del terreno puede modificar este registro.'
        return False

    def puede_ver(self, persona, obj):
        return False


class ViviendaPermission(AlcanceTerrenoPermission):
    """Además del administrador del terreno, quienes participan en la vivienda pueden verla."""

    def puede_ver(self, persona, vivienda):
        return participa(persona, vivienda)


class PuntoAccesoPermission(AlcanceTerrenoPermission):
    """Solo el administrador del terreno ve y gestiona sus puntos de acceso."""


# ---------------------------------------------------------------- operación del negocio

class ParticipacionPermission(BasePermission):
    """Asignar una persona a una vivienda (POST /api/viviendas/{id}/participaciones/).

    - Staff: asigna cualquier rol en cualquier vivienda.
    - PROPIETARIO_ADMIN: solo el staff.
    - PROPIETARIO, ARRENDATARIO o CONVIVIENTE: el staff o quien tiene
      participación activa PROPIETARIO_ADMIN en ESA vivienda.
    - El administrador del terreno no gestiona a las personas de las viviendas.
    - Ver las participaciones: staff o quienes participan en la vivienda.

    La regla se evalúa sobre el rol pedido antes de validar y guardar: un
    rechazo no modifica la BD.
    """

    def has_object_permission(self, request, view, vivienda):
        user = request.user
        persona = persona_de(user)
        if request.method in SAFE_METHODS:
            if user.is_staff or participa(persona, vivienda):
                return True
            self.message = 'Solo quienes participan en esta vivienda pueden ver sus participaciones.'
            return False

        if user.is_staff:
            return True
        datos = request.data if hasattr(request.data, 'get') else {}
        rol = datos.get('rol')
        if rol == PROPIETARIO_ADMIN:
            self.message = 'Solo el personal (staff) puede asignar el rol PROPIETARIO_ADMIN.'
            return False
        es_propietario_admin = participa(persona, vivienda, PROPIETARIO_ADMIN)
        if rol in ParticipacionVivienda.Rol.values:
            self.message = 'Solo el staff o un propietario administrador activo de esta vivienda puede asignar este rol.'
            return es_propietario_admin
        # Rol ausente o inválido: si podría asignar, la validación explica el error con un 400.
        self.message = 'No tienes autoridad para asignar personas en esta vivienda.'
        return es_propietario_admin
