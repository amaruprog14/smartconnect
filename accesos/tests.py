from rest_framework.test import APITestCase
from accesos.models import PuntoAcceso
from config.pruebas import cliente, crear_escenario, ids


class PuntosAccesoTests(APITestCase):
    def setUp(self):
        self.e = crear_escenario()
        self.ana = cliente(self.e.u_ana)

    def test_crud_del_administrador_del_terreno(self):
        comun = self.ana.post('/api/puntos-acceso/', {
            'terreno': self.e.t1.pk, 'nombre': 'Porton sur', 'tipo': 'PORTON',
        }, format='json')
        self.assertEqual(comun.status_code, 201)
        punto = PuntoAcceso.objects.get(pk=comun.data['id'])
        self.assertEqual((punto.terreno, punto.vivienda, punto.activo), (self.e.t1, None, True))

        privado = self.ana.post('/api/puntos-acceso/', {
            'terreno': self.e.t1.pk, 'vivienda': self.e.v1.pk, 'nombre': 'Puerta trasera', 'tipo': 'PUERTA',
        }, format='json')
        self.assertEqual(privado.status_code, 201)
        self.assertEqual(PuntoAcceso.objects.get(pk=privado.data['id']).vivienda, self.e.v1)

        url = f'/api/puntos-acceso/{punto.pk}/'
        self.assertEqual(self.ana.get(url).status_code, 200)
        self.assertEqual(self.ana.put(url, {'terreno': self.e.t2.pk, 'vivienda': None, 'nombre': 'Porton T2',
                                            'tipo': 'PORTON', 'activo': True}, format='json').status_code, 200)
        self.assertEqual(self.ana.patch(url, {'activo': False}, format='json').status_code, 200)
        punto.refresh_from_db()
        self.assertEqual((punto.terreno, punto.nombre, punto.activo), (self.e.t2, 'Porton T2', False))
        self.assertEqual(self.ana.delete(url).status_code, 204)
        self.assertEqual(self.ana.get(url).status_code, 404)

    def test_vivienda_de_otro_terreno_responde_400(self):
        antes = PuntoAcceso.objects.count()
        response = self.ana.post('/api/puntos-acceso/', {
            'terreno': self.e.t1.pk, 'vivienda': self.e.v3.pk, 'nombre': 'Invalido', 'tipo': 'PUERTA',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('vivienda', response.data)
        self.assertEqual(PuntoAcceso.objects.count(), antes)
        # En PATCH también: P2 es de V1 (T1) y no puede pasar a T2 sin cambiar su vivienda.
        response = self.ana.patch(f'/api/puntos-acceso/{self.e.p2.pk}/', {'terreno': self.e.t2.pk}, format='json')
        self.assertEqual(response.status_code, 400)
        self.e.p2.refresh_from_db()
        self.assertEqual(self.e.p2.terreno, self.e.t1)

    def test_listado_filtrado_por_alcance(self):
        e = self.e
        self.assertEqual(ids(self.ana.get('/api/puntos-acceso/')), [e.p1.pk, e.p2.pk])
        # Diego vive en V1, pero solo ve los puntos del terreno que administra.
        self.assertEqual(ids(cliente(e.u_diego).get('/api/puntos-acceso/')), [e.p3.pk])
        self.assertEqual(cliente(e.u_sofia).get('/api/puntos-acceso/').data, [])

    def test_punto_ajeno_responde_403_sin_cambios(self):
        diego = cliente(self.e.u_diego)
        self.assertEqual(diego.get(f'/api/puntos-acceso/{self.e.p1.pk}/').status_code, 403)
        self.assertEqual(diego.patch(f'/api/puntos-acceso/{self.e.p1.pk}/', {'activo': False},
                                     format='json').status_code, 403)
        self.assertEqual(diego.delete(f'/api/puntos-acceso/{self.e.p1.pk}/').status_code, 403)
        antes = PuntoAcceso.objects.count()
        self.assertEqual(diego.post('/api/puntos-acceso/', {
            'terreno': self.e.t1.pk, 'nombre': 'Intruso', 'tipo': 'PUERTA',
        }, format='json').status_code, 403)
        self.assertEqual(cliente(self.e.u_sofia).post('/api/puntos-acceso/', {
            'terreno': self.e.t1.pk, 'nombre': 'Intruso', 'tipo': 'PUERTA',
        }, format='json').status_code, 403)
        self.assertEqual(PuntoAcceso.objects.count(), antes)
        self.e.p1.refresh_from_db()
        self.assertTrue(self.e.p1.activo)
