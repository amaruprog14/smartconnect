"""Escenario común para los tests de permisos y de la operación del negocio.

- staff: cuenta is_staff, sin persona.
- ana: administra T1 y T2.
- diego: administra T3 y es PROPIETARIO_ADMIN de V1 (Casa 1, en T1).
- carla: sin cuenta, ARRENDATARIO de V1.
- sofia: cuenta y persona, sin terrenos ni viviendas.
- sin_persona: cuenta sin persona vinculada.
- Puntos: P1 común de T1, P2 de V1 y P3 común de T3.

Las cuentas no tienen contraseña: los tests usan force_authenticate. El login
real con JWT se prueba en personas/tests.py.
"""
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accesos.models import PuntoAcceso
from personas.models import Persona
from terrenos.models import Terreno
from viviendas.models import ParticipacionVivienda, Vivienda


def crear_escenario():
    User = get_user_model()
    e = SimpleNamespace()
    e.u_staff = User.objects.create_user('staff', is_staff=True)
    e.u_ana = User.objects.create_user('ana')
    e.u_diego = User.objects.create_user('diego')
    e.u_sofia = User.objects.create_user('sofia')
    e.u_sin_persona = User.objects.create_user('sin_persona')

    e.ana = Persona.objects.create(codigo='P-ANA', nombres='Ana', apellidos='Rojas', email='ana@example.com',
                                   usuario=e.u_ana)
    e.diego = Persona.objects.create(codigo='P-DIEGO', nombres='Diego', apellidos='Soto',
                                     email='diego@example.com', usuario=e.u_diego)
    e.carla = Persona.objects.create(codigo='P-CARLA', nombres='Carla', apellidos='Fuentes',
                                     email='carla@example.com')
    e.sofia = Persona.objects.create(codigo='P-SOFIA', nombres='Sofia', apellidos='Vidal',
                                     email='sofia@example.com', usuario=e.u_sofia)

    e.t1 = Terreno.objects.create(codigo='T1', nombre='Terreno 1', direccion='Calle 1', administrador=e.ana)
    e.t2 = Terreno.objects.create(codigo='T2', nombre='Terreno 2', direccion='Calle 2', administrador=e.ana)
    e.t3 = Terreno.objects.create(codigo='T3', nombre='Terreno 3', direccion='Calle 3', administrador=e.diego)

    e.v1 = Vivienda.objects.create(terreno=e.t1, identificador='Casa 1', tipo=Vivienda.Tipo.CASA)
    e.v3 = Vivienda.objects.create(terreno=e.t3, identificador='Depto 101', tipo=Vivienda.Tipo.DEPARTAMENTO)
    Rol = ParticipacionVivienda.Rol
    e.pa_diego = ParticipacionVivienda.objects.create(persona=e.diego, vivienda=e.v1, rol=Rol.PROPIETARIO_ADMIN)
    ParticipacionVivienda.objects.create(persona=e.carla, vivienda=e.v1, rol=Rol.ARRENDATARIO)

    e.p1 = PuntoAcceso.objects.create(terreno=e.t1, nombre='Porton', tipo=PuntoAcceso.Tipo.PORTON)
    e.p2 = PuntoAcceso.objects.create(terreno=e.t1, vivienda=e.v1, nombre='Puerta Casa 1',
                                      tipo=PuntoAcceso.Tipo.PUERTA)
    e.p3 = PuntoAcceso.objects.create(terreno=e.t3, nombre='Porton T3', tipo=PuntoAcceso.Tipo.PORTON)
    return e


def cliente(usuario):
    """APIClient autenticado como el usuario indicado."""
    client = APIClient()
    client.force_authenticate(usuario)
    return client


def ids(response):
    return sorted(item['id'] for item in response.data)
