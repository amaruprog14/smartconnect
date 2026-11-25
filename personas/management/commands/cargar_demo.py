from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from accesos.models import PuntoAcceso
from personas.models import Persona
from terrenos.models import Terreno
from viviendas.models import ParticipacionVivienda, Vivienda

# Contraseña de práctica para todas las cuentas de demostración. Solo para localhost.
CLAVE_DEMO = 'Demo1234!'
Rol = ParticipacionVivienda.Rol


class Command(BaseCommand):
    help = 'Carga o actualiza datos ficticios y cuentas de prueba sin duplicarlos.'

    def cuenta(self, username, staff=False):
        usuario, _ = get_user_model().objects.get_or_create(username=username)
        usuario.is_staff = staff
        usuario.is_superuser = staff  # El staff de la demo también puede entrar a /admin/.
        usuario.set_password(CLAVE_DEMO)
        usuario.save()
        return usuario

    def persona(self, codigo, nombres, apellidos, email, usuario=None):
        persona, _ = Persona.objects.update_or_create(codigo=codigo, defaults={
            'nombres': nombres, 'apellidos': apellidos, 'email': email, 'usuario': usuario,
        })
        return persona

    @transaction.atomic
    def handle(self, *args, **options):
        self.cuenta('staff', staff=True)
        ana = self.persona('PER-001', 'Ana', 'Rojas', 'ana@example.com', self.cuenta('ana'))
        diego = self.persona('PER-002', 'Diego', 'Soto', 'diego@example.com', self.cuenta('diego'))
        carla = self.persona('PER-003', 'Carla', 'Fuentes', 'carla@example.com')
        pedro = self.persona('PER-004', 'Pedro', 'Lagos', 'pedro@example.com')
        # Persona con cuenta pero sin terrenos ni viviendas: muestra listados vacíos y 403.
        sofia = self.persona('PER-005', 'Sofia', 'Vidal', 'sofia@example.com', self.cuenta('sofia'))

        # Ana administra dos terrenos; Diego, uno.
        terrenos = {}
        for codigo, nombre, direccion, administrador in [
            ('TER-001', 'Conjunto Los Aromos', 'Calle Ficticia 100', ana),
            ('TER-002', 'Conjunto Las Palmas', 'Calle Ficticia 200', ana),
            ('TER-003', 'Conjunto El Bosque', 'Calle Ficticia 300', diego),
        ]:
            terrenos[codigo], _ = Terreno.objects.update_or_create(codigo=codigo, defaults={
                'nombre': nombre, 'direccion': direccion, 'administrador': administrador,
            })

        # Casa 1 se crea primero: la colección de Apidog la usa como la primera vivienda de Diego.
        viviendas = {}
        for clave, terreno, identificador, tipo in [
            ('casa1', 'TER-001', 'Casa 1', Vivienda.Tipo.CASA),
            ('depto101', 'TER-003', 'Depto 101', Vivienda.Tipo.DEPARTAMENTO),
            ('casa5', 'TER-002', 'Casa 5', Vivienda.Tipo.CASA),
        ]:
            viviendas[clave], _ = Vivienda.objects.update_or_create(
                terreno=terrenos[terreno], identificador=identificador, defaults={'tipo': tipo},
            )

        for persona, vivienda, rol in [
            # Propietario administrador con un arrendatario y un conviviente.
            (diego, 'casa1', Rol.PROPIETARIO_ADMIN),
            (carla, 'casa1', Rol.ARRENDATARIO),
            (pedro, 'casa1', Rol.CONVIVIENTE),
            # Carla tiene viviendas en dos terrenos: arrendataria en TER-001 y propietaria en TER-003.
            (carla, 'depto101', Rol.PROPIETARIO),
            # Diego administra TER-003 y arrienda en TER-002.
            (diego, 'casa5', Rol.ARRENDATARIO),
        ]:
            ParticipacionVivienda.objects.update_or_create(
                persona=persona, vivienda=viviendas[vivienda], defaults={'rol': rol, 'activa': True},
            )

        # Accesos comunes (sin vivienda) y uno privado de Casa 1.
        for terreno, nombre, tipo, vivienda in [
            ('TER-001', 'Porton principal', PuntoAcceso.Tipo.PORTON, None),
            ('TER-001', 'Puerta peatonal', PuntoAcceso.Tipo.PUERTA, None),
            ('TER-001', 'Puerta Casa 1', PuntoAcceso.Tipo.PUERTA, viviendas['casa1']),
            ('TER-003', 'Porton El Bosque', PuntoAcceso.Tipo.PORTON, None),
        ]:
            PuntoAcceso.objects.update_or_create(terreno=terrenos[terreno], nombre=nombre, defaults={
                'tipo': tipo, 'vivienda': vivienda, 'activo': True,
            })

        if options['verbosity'] == 0:
            return
        for codigo, terreno in terrenos.items():
            self.stdout.write(f'{codigo}: id={terreno.pk}, administrador={terreno.administrador}')
        self.stdout.write(self.style.SUCCESS(
            f'Datos ficticios listos. Cuentas staff, ana, diego y sofia con clave {CLAVE_DEMO}. '
            f'Personas: Ana id={ana.pk}, Diego id={diego.pk}, Sofia id={sofia.pk}.'
        ))
