import json
import re
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase
from accesos.models import PuntoAcceso
from config.pruebas import cliente, crear_escenario, ids
from personas.models import Persona
from terrenos.models import Terreno
from viviendas.models import ParticipacionVivienda, Vivienda

# Hasher rápido solo para tests que crean cuentas con contraseña.
HASHER_RAPIDO = ['django.contrib.auth.hashers.MD5PasswordHasher']
COLECCION = Path(__file__).resolve().parent.parent / 'apidog' / 'SmartConnect.postman_collection.json'
ESPERADO = re.compile(r'Esperado: (\d{3})\.', re.IGNORECASE)
VARIABLE = re.compile(r'\{\{(\w+)\}\}')
# Única forma de script que usa la colección para guardar valores de la respuesta.
GUARDAR = re.compile(r'pm\.collectionVariables\.set\("(\w+)", pm\.response\.json\(\)((?:\.\w+|\[\d+\])*)\)')


def peticiones(items):
    """Recorre las carpetas de la colección en orden."""
    for item in items:
        if 'item' in item:
            yield from peticiones(item['item'])
        else:
            yield item


def extraer(datos, ruta):
    """Aplica una ruta como .access o [0].id sobre el JSON de la respuesta."""
    for clave, indice in re.findall(r'\.(\w+)|\[(\d+)\]', ruta):
        datos = datos[clave] if clave else datos[int(indice)]
    return datos


def conteos():
    modelos = [get_user_model(), Persona, Terreno, Vivienda, ParticipacionVivienda, PuntoAcceso]
    return {modelo.__name__: modelo.objects.count() for modelo in modelos}


@override_settings(PASSWORD_HASHERS=HASHER_RAPIDO)
class ColeccionApidogTests(APITestCase):
    def test_coleccion_completa_y_persistencia(self):
        """Ejecuta en orden todas las peticiones que se importan en Apidog, con login JWT real."""
        call_command('cargar_demo', verbosity=0)
        inicial = conteos()
        coleccion = json.loads(COLECCION.read_text(encoding='utf-8'))
        variables = {v['key']: v['value'] for v in coleccion['variable']}

        def reemplazar(texto):
            texto = texto.replace('{{base_url}}', '')

            def valor(match):
                nombre = match.group(1)
                self.assertNotEqual(variables.get(nombre, ''), '', f'{item["name"]}: falta la variable {nombre}')
                return str(variables[nombre])
            return VARIABLE.sub(valor, texto)

        total = 0
        for item in peticiones(coleccion['item']):
            total += 1
            req = item['request']
            esperado = int(ESPERADO.search(req['description']).group(1))
            url = reemplazar(req['url'])
            raw = reemplazar(req.get('body', {}).get('raw', ''))
            extra = {}
            for header in req['header']:
                if header['key'] == 'Authorization':
                    extra['HTTP_AUTHORIZATION'] = reemplazar(header['value'])
            antes = conteos()
            response = getattr(self.client, req['method'].lower())(
                url, json.loads(raw) if raw else None, format='json', **extra,
            )
            self.assertEqual(response.status_code, esperado, (item['name'], getattr(response, 'data', None)))
            if esperado >= 400:
                self.assertEqual(conteos(), antes, f'{item["name"]}: un rechazo modificó la BD')
            for linea in item['event'][0]['script']['exec']:
                for variable, ruta in GUARDAR.findall(linea):
                    variables[variable] = extraer(response.data, ruta)
            self.comprobar(item['name'][:2], response, variables)

        self.assertEqual(total, 67)
        # La colección limpia lo que crea: quedan exactamente los datos de cargar_demo.
        self.assertEqual(conteos(), inicial)
        self.assertFalse(Persona.objects.filter(codigo='PER-PRUEBA').exists())

    def comprobar(self, numero, response, v):
        """Verificaciones de lo que quedó guardado en los pasos clave."""
        datos = response.data
        if numero == '01':
            self.assertIn('refresh', datos)
            self.access_login = datos['access']
        elif numero == '02':
            self.assertNotEqual(datos['access'], self.access_login)
        elif numero == '09':
            self.assertEqual([p['codigo'] for p in datos], ['PER-001'])
        elif numero == '11':
            self.assertEqual([p['codigo'] for p in datos], ['PER-002'])
        elif numero == '15':
            self.assertEqual(Persona.objects.get(pk=v['persona_id']).nombres, 'Camila')
        elif numero == '20':
            self.assertEqual(datos['administrador'], v['persona_id'])
            self.assertEqual(datos['administrador_nombre'], 'Camila Perez')
        elif numero == '22':
            terreno = Terreno.objects.get(pk=v['terreno_id'])
            self.assertEqual((terreno.nombre, terreno.direccion), ('Conjunto actualizado', 'Pasaje Ficticio 501'))
        elif numero == '25':
            self.assertEqual(Terreno.objects.get(pk=v['terreno_id']).administrador_id, v['ana_persona_id'])
        elif numero == '26':
            # El filtro devuelve solo Casa 1 de TER-001, sin depender del orden de cargar_demo.
            self.assertEqual([(d['identificador'], d['terreno_nombre']) for d in datos],
                             [('Casa 1', 'Conjunto Los Aromos')])
        elif numero == '29':
            self.assertEqual([d['id'] for d in datos], [v['vivienda_id']])
        elif numero == '32':
            vivienda = Vivienda.objects.get(pk=v['vivienda_id'])
            self.assertEqual((vivienda.identificador, vivienda.tipo), ('Casa A1', 'DEPARTAMENTO'))
        elif numero == '36':
            self.assertEqual(PuntoAcceso.objects.get(pk=v['punto_vivienda_id']).vivienda_id, v['vivienda_id'])
        elif numero == '37':
            self.assertIn('vivienda', datos)
        elif numero == '41':
            self.assertFalse(PuntoAcceso.objects.get(pk=v['punto_id']).activo)
        elif numero == '43':
            self.assertTrue(ParticipacionVivienda.objects.filter(
                persona_id=v['persona_id'], vivienda_id=v['vivienda_demo_id'], rol='ARRENDATARIO', activa=True,
            ).exists())
        elif numero == '44':
            self.assertTrue(ParticipacionVivienda.objects.filter(
                persona_id=v['persona_id'], vivienda_id=v['vivienda_id'], rol='CONVIVIENTE', activa=True,
            ).exists())
        elif numero == '49':
            self.assertEqual(sorted(p['rol'] for p in datos),
                             ['ARRENDATARIO', 'ARRENDATARIO', 'CONVIVIENTE', 'PROPIETARIO_ADMIN'])
        elif numero == '50':
            self.assertIn('PROPIETARIO_ADMIN', datos['detail'])
            self.assertTrue(ParticipacionVivienda.objects.filter(
                persona_id=v['diego_persona_id'], vivienda_id=v['vivienda_demo_id'], rol='PROPIETARIO_ADMIN',
                activa=True,
            ).exists())
        elif numero == '55':
            self.assertIn('administrador', datos['detail'])
            self.assertEqual(Terreno.objects.get(pk=v['terreno_id']).administrador_id, v['ana_persona_id'])
        elif numero == '56':
            self.assertEqual(datos, [])
        elif numero == '59':
            # CASCADE: no quedan participaciones de la persona de prueba.
            self.assertFalse(ParticipacionVivienda.objects.filter(persona_id=v['persona_id']).exists())


@override_settings(PASSWORD_HASHERS=HASHER_RAPIDO)
class AutenticacionJWTTests(APITestCase):
    def setUp(self):
        get_user_model().objects.create_user('ana', password='Demo1234!')

    def login(self):
        return self.client.post('/api/token/', {'username': 'ana', 'password': 'Demo1234!'}, format='json')

    def test_sin_token_responde_401_y_no_guarda(self):
        for url in ('/api/personas/', '/api/terrenos/', '/api/viviendas/', '/api/puntos-acceso/'):
            self.assertEqual(self.client.get(url).status_code, 401, url)
        response = self.client.post('/api/personas/', {
            'codigo': 'A', 'nombres': 'Ana', 'apellidos': 'Rojas', 'email': 'a@example.com',
        }, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Persona.objects.exists())

    def test_token_invalido_responde_401(self):
        response = self.client.get('/api/personas/', HTTP_AUTHORIZATION='Bearer token-falso')
        self.assertEqual(response.status_code, 401)

    def test_login_entrega_access_y_refresh(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        protegida = self.client.get('/api/personas/', HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        self.assertEqual(protegida.status_code, 200)

    def test_refresh_entrega_un_access_nuevo_que_funciona(self):
        tokens = self.login().data
        response = self.client.post('/api/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['access'], tokens['access'])
        protegida = self.client.get('/api/terrenos/', HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        self.assertEqual(protegida.status_code, 200)

    def test_login_y_refresh_invalidos_responden_401(self):
        response = self.client.post('/api/token/', {'username': 'ana', 'password': 'otra'}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access', response.data)
        response = self.client.post('/api/token/refresh/', {'refresh': 'no-es-un-token'}, format='json')
        self.assertEqual(response.status_code, 401)


class PersonasStaffTests(APITestCase):
    def setUp(self):
        # El staff tiene acceso completo al CRUD de personas y terrenos.
        self.client.force_authenticate(get_user_model().objects.create_user('staff', is_staff=True))

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

    @override_settings(PASSWORD_HASHERS=HASHER_RAPIDO)
    def test_datos_demo_no_se_duplican_y_cubren_los_escenarios(self):
        call_command('cargar_demo', verbosity=0)
        call_command('cargar_demo', verbosity=0)
        self.assertEqual(Persona.objects.count(), 5)
        self.assertEqual(Terreno.objects.count(), 3)
        self.assertEqual(Vivienda.objects.count(), 3)
        self.assertEqual(ParticipacionVivienda.objects.count(), 5)
        self.assertEqual(PuntoAcceso.objects.count(), 4)
        # Cuentas con contraseña de demo, vinculadas a su persona (salvo staff).
        for username in ('staff', 'ana', 'diego', 'sofia'):
            self.assertTrue(get_user_model().objects.get(username=username).check_password('Demo1234!'))
        self.assertTrue(get_user_model().objects.get(username='staff').is_staff)
        self.assertEqual(Persona.objects.get(usuario__username='sofia').participaciones.count(), 0)
        # Ana administra dos terrenos.
        ana = Persona.objects.get(codigo='PER-001')
        self.assertEqual(ana.terrenos_administrados.count(), 2)
        # Carla tiene viviendas en dos terrenos: propietaria en uno y arrendataria en otro.
        carla = Persona.objects.get(codigo='PER-003')
        roles = {p.vivienda.terreno.codigo: p.rol for p in carla.participaciones.select_related('vivienda__terreno')}
        self.assertEqual(roles, {'TER-001': 'ARRENDATARIO', 'TER-003': 'PROPIETARIO'})
        # Casa 1: propietario administrador con un arrendatario y un conviviente.
        casa1 = Vivienda.objects.get(terreno__codigo='TER-001', identificador='Casa 1')
        self.assertEqual(sorted(casa1.participaciones.values_list('rol', flat=True)),
                         ['ARRENDATARIO', 'CONVIVIENTE', 'PROPIETARIO_ADMIN'])
        # Accesos comunes y uno ligado a una vivienda.
        self.assertEqual(PuntoAcceso.objects.filter(vivienda__isnull=True).count(), 3)
        self.assertEqual(PuntoAcceso.objects.get(vivienda=casa1).nombre, 'Puerta Casa 1')


class BorrarPropietarioAdminTests(APITestCase):
    """Borrar una persona no puede dejar una vivienda sin PROPIETARIO_ADMIN activo."""

    def setUp(self):
        self.e = crear_escenario()
        self.staff = cliente(self.e.u_staff)
        # Gabriel no administra terrenos: el 409 solo puede venir de la regla de participaciones.
        self.gabriel = Persona.objects.create(codigo='P-GABRIEL', nombres='Gabriel', apellidos='Mora',
                                              email='gabriel@example.com')
        ParticipacionVivienda.objects.create(persona=self.gabriel, vivienda=self.e.v3, rol='PROPIETARIO_ADMIN')
        ParticipacionVivienda.objects.create(persona=self.gabriel, vivienda=self.e.v1, rol='CONVIVIENTE')

    def test_unico_propietario_admin_responde_409_sin_cambios(self):
        antes = (Persona.objects.count(), ParticipacionVivienda.objects.count())
        response = self.staff.delete(f'/api/personas/{self.gabriel.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertIn('PROPIETARIO_ADMIN', response.data['detail'])
        self.assertIn('Depto 101', response.data['detail'])
        self.assertEqual((Persona.objects.count(), ParticipacionVivienda.objects.count()), antes)
        self.assertTrue(self.gabriel.participaciones.filter(vivienda=self.e.v3, activa=True).exists())

    def test_con_otro_propietario_admin_activo_se_elimina_en_cascada(self):
        ParticipacionVivienda.objects.create(persona=self.e.carla, vivienda=self.e.v3, rol='PROPIETARIO_ADMIN')
        response = self.staff.delete(f'/api/personas/{self.gabriel.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Persona.objects.filter(pk=self.gabriel.pk).exists())
        self.assertFalse(ParticipacionVivienda.objects.filter(persona_id=self.gabriel.pk).exists())
        self.assertTrue(ParticipacionVivienda.objects.filter(persona=self.e.carla, vivienda=self.e.v3).exists())

    def test_otro_propietario_admin_inactivo_no_cuenta(self):
        ParticipacionVivienda.objects.create(persona=self.e.carla, vivienda=self.e.v3, rol='PROPIETARIO_ADMIN',
                                             activa=False)
        self.assertEqual(self.staff.delete(f'/api/personas/{self.gabriel.pk}/').status_code, 409)
        self.assertTrue(Persona.objects.filter(pk=self.gabriel.pk).exists())

    def test_participacion_propietario_admin_inactiva_no_bloquea(self):
        self.gabriel.participaciones.filter(vivienda=self.e.v3).update(activa=False)
        self.assertEqual(self.staff.delete(f'/api/personas/{self.gabriel.pk}/').status_code, 204)


class AlcancePersonasTests(APITestCase):
    def setUp(self):
        self.e = crear_escenario()

    def test_usuario_normal_lista_y_edita_solo_su_persona(self):
        ana = cliente(self.e.u_ana)
        self.assertEqual(ids(ana.get('/api/personas/')), [self.e.ana.pk])
        response = ana.patch(f'/api/personas/{self.e.ana.pk}/', {'nombres': 'Ana Maria'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.e.ana.refresh_from_db()
        self.assertEqual(self.e.ana.nombres, 'Ana Maria')

    def test_editar_o_ver_otra_persona_responde_403(self):
        ana = cliente(self.e.u_ana)
        self.assertEqual(ana.get(f'/api/personas/{self.e.diego.pk}/').status_code, 403)
        response = ana.patch(f'/api/personas/{self.e.diego.pk}/', {'nombres': 'X'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.e.diego.refresh_from_db()
        self.assertEqual(self.e.diego.nombres, 'Diego')

    def test_crear_y_eliminar_personas_solo_staff(self):
        ana = cliente(self.e.u_ana)
        antes = Persona.objects.count()
        nueva = {'codigo': 'N', 'nombres': 'N', 'apellidos': 'N', 'email': 'n@example.com'}
        self.assertEqual(ana.post('/api/personas/', nueva, format='json').status_code, 403)
        self.assertEqual(ana.delete(f'/api/personas/{self.e.sofia.pk}/').status_code, 403)
        self.assertEqual(Persona.objects.count(), antes)
        staff = cliente(self.e.u_staff)
        self.assertEqual(staff.post('/api/personas/', nueva, format='json').status_code, 201)
        self.assertEqual(len(staff.get('/api/personas/').data), antes + 1)

    def test_usuario_sin_persona_ve_listados_vacios_y_no_escribe(self):
        sin_persona = cliente(self.e.u_sin_persona)
        for url in ('/api/personas/', '/api/terrenos/', '/api/viviendas/', '/api/puntos-acceso/'):
            response = sin_persona.get(url)
            self.assertEqual((response.status_code, response.data), (200, []), url)
        self.assertEqual(sin_persona.patch(f'/api/personas/{self.e.ana.pk}/', {'nombres': 'X'},
                                           format='json').status_code, 403)
        self.assertEqual(sin_persona.patch(f'/api/terrenos/{self.e.t1.pk}/', {'nombre': 'X'},
                                           format='json').status_code, 403)
        self.assertEqual(sin_persona.post('/api/viviendas/', {
            'terreno': self.e.t1.pk, 'identificador': 'X', 'tipo': 'CASA',
        }, format='json').status_code, 403)
        self.assertEqual(sin_persona.post('/api/puntos-acceso/', {
            'terreno': self.e.t1.pk, 'nombre': 'X', 'tipo': 'PUERTA',
        }, format='json').status_code, 403)
        self.assertEqual(Vivienda.objects.count(), 2)
        self.assertEqual(PuntoAcceso.objects.count(), 3)
