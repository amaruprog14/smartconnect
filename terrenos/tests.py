from rest_framework.test import APITestCase
from config.pruebas import cliente, crear_escenario, ids
from terrenos.models import Terreno


class AlcanceTerrenosTests(APITestCase):
    def setUp(self):
        self.e = crear_escenario()

    def test_listado_filtrado_por_alcance(self):
        e = self.e
        # Ana administra T1 y T2.
        self.assertEqual(ids(cliente(e.u_ana).get('/api/terrenos/')), [e.t1.pk, e.t2.pk])
        # Diego administra T3 y tiene una vivienda en T1.
        self.assertEqual(ids(cliente(e.u_diego).get('/api/terrenos/')), [e.t1.pk, e.t3.pk])
        self.assertEqual(cliente(e.u_sofia).get('/api/terrenos/').data, [])
        self.assertEqual(len(cliente(e.u_staff).get('/api/terrenos/').data), 3)

    def test_administrador_edita_su_terreno(self):
        response = cliente(self.e.u_ana).patch(f'/api/terrenos/{self.e.t1.pk}/', {'nombre': 'Nuevo'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.e.t1.refresh_from_db()
        self.assertEqual(self.e.t1.nombre, 'Nuevo')

    def test_terreno_ajeno_responde_403_sin_cambios(self):
        diego = cliente(self.e.u_diego)
        # Diego vive en T1: puede verlo, pero no editarlo.
        self.assertEqual(diego.get(f'/api/terrenos/{self.e.t1.pk}/').status_code, 200)
        response = diego.patch(f'/api/terrenos/{self.e.t1.pk}/', {'nombre': 'Ajeno'}, format='json')
        self.assertEqual(response.status_code, 403)
        # T2 no es suyo ni vive allí: ni siquiera lo ve.
        self.assertEqual(diego.get(f'/api/terrenos/{self.e.t2.pk}/').status_code, 403)
        self.e.t1.refresh_from_db()
        self.assertEqual(self.e.t1.nombre, 'Terreno 1')

    def test_crear_y_eliminar_solo_staff(self):
        nuevo = {'codigo': 'T9', 'nombre': 'Nuevo', 'direccion': 'Calle 9', 'administrador': self.e.ana.pk}
        ana = cliente(self.e.u_ana)
        self.assertEqual(ana.post('/api/terrenos/', nuevo, format='json').status_code, 403)
        self.assertEqual(ana.delete(f'/api/terrenos/{self.e.t2.pk}/').status_code, 403)
        self.assertEqual(Terreno.objects.count(), 3)
        staff = cliente(self.e.u_staff)
        self.assertEqual(staff.post('/api/terrenos/', nuevo, format='json').status_code, 201)
        self.assertEqual(staff.delete(f'/api/terrenos/{self.e.t2.pk}/').status_code, 204)
        self.assertEqual(sorted(Terreno.objects.values_list('codigo', flat=True)), ['T1', 'T3', 'T9'])

    def test_terreno_con_viviendas_o_puntos_responde_409(self):
        staff = cliente(self.e.u_staff)
        response = staff.delete(f'/api/terrenos/{self.e.t1.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertIn('viviendas', response.data['detail'])
        self.assertTrue(Terreno.objects.filter(pk=self.e.t1.pk).exists())
