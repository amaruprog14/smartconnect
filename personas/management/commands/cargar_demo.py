from django.core.management.base import BaseCommand
from django.db import transaction
from personas.models import Persona
from terrenos.models import Terreno

class Command(BaseCommand):
    help = 'Carga o actualiza datos ficticios sin duplicarlos.'

    @transaction.atomic
    def handle(self, *args, **options):
        ana, _ = Persona.objects.update_or_create(codigo='PER-001', defaults={
            'nombres': 'Ana', 'apellidos': 'Rojas', 'email': 'ana@example.com',
        })
        diego, _ = Persona.objects.update_or_create(codigo='PER-002', defaults={
            'nombres': 'Diego', 'apellidos': 'Soto', 'email': 'diego@example.com',
        })
        for codigo, nombre, direccion, administrador in [
            ('TER-001', 'Conjunto Los Aromos', 'Calle Ficticia 100', ana),
            ('TER-002', 'Conjunto Las Palmas', 'Calle Ficticia 200', ana),
            ('TER-003', 'Conjunto El Bosque', 'Calle Ficticia 300', diego),
        ]:
            terreno, _ = Terreno.objects.update_or_create(codigo=codigo, defaults={
                'nombre': nombre, 'direccion': direccion, 'administrador': administrador,
            })
            self.stdout.write(f'{terreno.codigo}: id={terreno.pk}, administrador={administrador.pk}')
        self.stdout.write(self.style.SUCCESS(
            f'Datos ficticios listos. Ana id={ana.pk}; Diego id={diego.pk}.'
        ))
