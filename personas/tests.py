import json
from pathlib import Path
from django.core.management import call_command
from rest_framework.test import APITestCase
from personas.models import Persona
from terrenos.models import Terreno


class EntregaUnoTests(APITestCase):
    def test_coleccion_completa_y_persistencia(self):
        """Ejecuta las mismas 18 peticiones que se importan en Apidog."""
        path = Path(__file__).resolve().parent.parent / 'docs/SmartConnect.postman_collection.json'
        collection = json.loads(path.read_text(encoding='utf-8'))
        variables = {}
        for item in collection['item']:
            req = item['request']
            url = req['url'].replace('{{base_url}}', '')
            raw = req.get('body', {}).get('raw', '')
            for key, value in variables.items():
                url = url.replace('{{' + key + '}}', str(value))
                raw = raw.replace('{{' + key + '}}', str(value))
            expected = int(req['description'].split(': ')[1].split('.')[0])
            body = json.loads(raw) if raw else None
            response = getattr(self.client, req['method'].lower())(url, body, format='json')
            self.assertEqual(response.status_code, expected, (item['name'], getattr(response, 'data', None)))
            if req['method'] == 'POST' and expected == 201:
                key = 'persona_id' if '/personas/' in url else 'terreno_id'
                variables[key] = response.data['id']
            if item['name'].startswith('05'):
                self.assertEqual(Persona.objects.get(pk=variables['persona_id']).nombres, 'Camila')
            if item['name'].startswith('10'):
                self.assertEqual(response.data['administrador'], variables['persona_id'])
                self.assertEqual(response.data['administrador_nombre'], 'Camila Perez')
            if item['name'].startswith('12'):
                terreno = Terreno.objects.get(pk=variables['terreno_id'])
                self.assertEqual(terreno.nombre, 'Conjunto actualizado')
                self.assertEqual(terreno.direccion, 'Pasaje Ficticio 501')
        self.assertFalse(Terreno.objects.exists())
        self.assertFalse(Persona.objects.exists())

    def test_datos_demo_no_se_duplican_y_administrador_repetido(self):
        call_command('cargar_demo', verbosity=0)
        call_command('cargar_demo', verbosity=0)
        self.assertEqual(Persona.objects.count(), 2)
        self.assertEqual(Terreno.objects.count(), 3)
        ana = Persona.objects.get(codigo='PER-001')
        self.assertEqual(ana.terrenos_administrados.count(), 2)

    def test_reasignacion_permite_eliminar_administrador_anterior(self):
        ana = Persona.objects.create(codigo='A', nombres='Ana', apellidos='Rojas', email='a@example.com')
        diego = Persona.objects.create(codigo='B', nombres='Diego', apellidos='Soto', email='b@example.com')
        terreno = Terreno.objects.create(codigo='T', nombre='Prueba', direccion='Calle 1', administrador=ana)
        self.assertEqual(self.client.delete(f'/api/personas/{ana.pk}/').status_code, 409)
        response = self.client.patch(f'/api/terrenos/{terreno.pk}/', {'administrador': diego.pk}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.delete(f'/api/personas/{ana.pk}/').status_code, 204)
        terreno.refresh_from_db()
        self.assertEqual(terreno.administrador_id, diego.pk)

    def test_campos_obligatorios_y_unicidad_email(self):
        persona = {'codigo': 'A', 'nombres': 'Ana', 'apellidos': 'Rojas', 'email': 'a@example.com'}
        self.assertEqual(self.client.post('/api/personas/', persona, format='json').status_code, 201)
        response = self.client.post('/api/personas/', {**persona, 'codigo': 'B'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        response = self.client.post('/api/personas/', {'codigo': 'C'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('nombres', response.data)
        self.assertEqual(self.client.post('/api/terrenos/', {
            'codigo': 'T', 'nombre': 'Terreno', 'direccion': 'Calle',
        }, format='json').status_code, 400)

    def test_put_exige_campos_completos_y_patch_es_parcial(self):
        persona = Persona.objects.create(codigo='A', nombres='Ana', apellidos='Rojas', email='a@example.com')
        url = f'/api/personas/{persona.pk}/'
        self.assertEqual(self.client.put(url, {'nombres': 'Cambio'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'nombres': 'Cambio'}, format='json').status_code, 200)
        persona.refresh_from_db()
        self.assertEqual(persona.nombres, 'Cambio')
        self.assertEqual(persona.email, 'a@example.com')
