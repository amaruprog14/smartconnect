from rest_framework.test import APIClient, APITestCase
from config.pruebas import cliente, crear_escenario, ids
from viviendas.models import ParticipacionVivienda, Vivienda


class ViviendasCrudTests(APITestCase):
    def setUp(self):
        self.e = crear_escenario()
        self.ana = cliente(self.e.u_ana)

    def test_crud_del_administrador_del_terreno(self):
        response = self.ana.post('/api/viviendas/', {
            'terreno': self.e.t1.pk, 'identificador': 'Casa 2', 'tipo': 'CASA',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        url = f'/api/viviendas/{response.data["id"]}/'
        vivienda = Vivienda.objects.get(pk=response.data['id'])
        self.assertEqual((vivienda.terreno, vivienda.identificador), (self.e.t1, 'Casa 2'))

        self.assertEqual(self.ana.get(url).data['terreno_nombre'], 'Terreno 1')
        response = self.ana.put(url, {'terreno': self.e.t2.pk, 'identificador': 'Depto 9',
                                      'tipo': 'DEPARTAMENTO'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.ana.patch(url, {'tipo': 'CASA'}, format='json').status_code, 200)
        vivienda.refresh_from_db()
        self.assertEqual((vivienda.terreno, vivienda.identificador, vivienda.tipo), (self.e.t2, 'Depto 9', 'CASA'))

        self.assertEqual(self.ana.delete(url).status_code, 204)
        self.assertEqual(self.ana.get(url).status_code, 404)

    def test_validaciones(self):
        antes = Vivienda.objects.count()
        duplicada = self.ana.post('/api/viviendas/', {
            'terreno': self.e.t1.pk, 'identificador': 'Casa 1', 'tipo': 'CASA',
        }, format='json')
        self.assertEqual(duplicada.status_code, 400)
        # El mismo identificador sí se permite en otro terreno.
        self.assertEqual(self.ana.post('/api/viviendas/', {
            'terreno': self.e.t2.pk, 'identificador': 'Casa 1', 'tipo': 'CASA',
        }, format='json').status_code, 201)
        tipo = self.ana.post('/api/viviendas/', {'terreno': self.e.t1.pk, 'identificador': 'X', 'tipo': 'CASTILLO'},
                             format='json')
        self.assertEqual(tipo.status_code, 400)
        self.assertIn('tipo', tipo.data)
        # V1 tiene puntos de acceso: no puede moverse a otro terreno.
        mover = self.ana.patch(f'/api/viviendas/{self.e.v1.pk}/', {'terreno': self.e.t2.pk}, format='json')
        self.assertEqual(mover.status_code, 400)
        self.assertEqual(Vivienda.objects.count(), antes + 1)

    def test_vivienda_con_puntos_o_participaciones_responde_409(self):
        response = self.ana.delete(f'/api/viviendas/{self.e.v1.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Vivienda.objects.filter(pk=self.e.v1.pk).exists())

    def test_listado_filtrado_por_alcance(self):
        e = self.e
        self.assertEqual(ids(self.ana.get('/api/viviendas/')), [e.v1.pk])
        # Diego participa en V1 y administra el terreno de V3.
        self.assertEqual(ids(cliente(e.u_diego).get('/api/viviendas/')), [e.v1.pk, e.v3.pk])
        self.assertEqual(cliente(e.u_sofia).get('/api/viviendas/').data, [])

    def test_vivienda_ajena_responde_403_sin_cambios(self):
        diego = cliente(self.e.u_diego)
        # Diego participa en V1, pero su terreno lo administra Ana.
        self.assertEqual(diego.get(f'/api/viviendas/{self.e.v1.pk}/').status_code, 200)
        self.assertEqual(diego.patch(f'/api/viviendas/{self.e.v1.pk}/', {'tipo': 'DEPARTAMENTO'},
                                     format='json').status_code, 403)
        self.assertEqual(diego.delete(f'/api/viviendas/{self.e.v1.pk}/').status_code, 403)
        self.assertEqual(cliente(self.e.u_sofia).get(f'/api/viviendas/{self.e.v1.pk}/').status_code, 403)
        # Ana no puede crear ni mover viviendas a un terreno que no administra.
        antes = Vivienda.objects.count()
        self.assertEqual(self.ana.post('/api/viviendas/', {
            'terreno': self.e.t3.pk, 'identificador': 'Intrusa', 'tipo': 'CASA',
        }, format='json').status_code, 403)
        self.assertEqual(Vivienda.objects.count(), antes)
        self.e.v1.refresh_from_db()
        self.assertEqual(self.e.v1.tipo, 'CASA')


class ParticipacionViviendaTests(APITestCase):
    """Operación del negocio: POST /api/viviendas/{id}/participaciones/."""

    def setUp(self):
        self.e = crear_escenario()
        self.url = f'/api/viviendas/{self.e.v1.pk}/participaciones/'

    def asignar(self, usuario, persona, rol):
        return cliente(usuario).post(self.url, {'persona': persona.pk, 'rol': rol}, format='json')

    def assertRechazo(self, response, codigo):
        """El rechazo responde el código esperado y no modifica la BD."""
        self.assertEqual(response.status_code, codigo, response.data)
        self.assertEqual(ParticipacionVivienda.objects.count(), self.antes)

    def test_asignacion_valida_por_propietario_admin(self):
        response = self.asignar(self.e.u_diego, self.e.sofia, 'CONVIVIENTE')
        self.assertEqual(response.status_code, 201)
        participacion = ParticipacionVivienda.objects.get(pk=response.data['id'])
        self.assertEqual(
            (participacion.persona, participacion.vivienda, participacion.rol, participacion.activa),
            (self.e.sofia, self.e.v1, 'CONVIVIENTE', True),
        )
        listado = cliente(self.e.u_diego).get(self.url)
        self.assertEqual(listado.status_code, 200)
        self.assertEqual(len(listado.data), 3)

    def test_rechazos_no_modifican_la_bd(self):
        self.antes = ParticipacionVivienda.objects.count()
        # Duplicado: Carla ya participa en V1.
        duplicada = self.asignar(self.e.u_diego, self.e.carla, 'CONVIVIENTE')
        self.assertRechazo(duplicada, 400)
        self.assertIn('persona', duplicada.data)
        # El administrador del terreno no gestiona a las personas de la vivienda.
        self.assertRechazo(self.asignar(self.e.u_ana, self.e.sofia, 'CONVIVIENTE'), 403)
        # Solo el staff asigna PROPIETARIO_ADMIN.
        self.assertRechazo(self.asignar(self.e.u_diego, self.e.sofia, 'PROPIETARIO_ADMIN'), 403)
        # Sin participación en la vivienda.
        self.assertRechazo(self.asignar(self.e.u_sofia, self.e.sofia, 'CONVIVIENTE'), 403)
        # Datos inválidos de alguien con autoridad.
        self.assertRechazo(self.asignar(self.e.u_diego, self.e.sofia, 'VECINO'), 400)
        self.assertRechazo(cliente(self.e.u_diego).post(self.url, {'rol': 'CONVIVIENTE'}, format='json'), 400)
        # Sin token.
        self.assertRechazo(APIClient().post(self.url, {'persona': self.e.sofia.pk, 'rol': 'CONVIVIENTE'},
                                            format='json'), 401)

    def test_propietario_admin_de_otra_vivienda_no_asigna_en_esta(self):
        ParticipacionVivienda.objects.create(persona=self.e.sofia, vivienda=self.e.v3, rol='PROPIETARIO_ADMIN')
        self.antes = ParticipacionVivienda.objects.count()
        self.assertRechazo(self.asignar(self.e.u_sofia, self.e.sofia, 'CONVIVIENTE'), 403)

    def test_propietario_admin_inactivo_no_asigna(self):
        self.e.pa_diego.activa = False
        self.e.pa_diego.save()
        self.antes = ParticipacionVivienda.objects.count()
        self.assertRechazo(self.asignar(self.e.u_diego, self.e.sofia, 'CONVIVIENTE'), 403)

    def test_staff_asigna_propietario_admin(self):
        response = self.asignar(self.e.u_staff, self.e.sofia, 'PROPIETARIO_ADMIN')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ParticipacionVivienda.objects.filter(
            persona=self.e.sofia, vivienda=self.e.v1, rol='PROPIETARIO_ADMIN').exists())
        # Con ese rol, Sofia ya puede asignar en V1.
        self.assertEqual(self.asignar(self.e.u_sofia, self.e.ana, 'ARRENDATARIO').status_code, 201)

    def test_staff_asigna_cualquier_rol_en_cualquier_vivienda(self):
        for persona, rol in [(self.e.sofia, 'CONVIVIENTE'), (self.e.ana, 'PROPIETARIO')]:
            response = self.asignar(self.e.u_staff, persona, rol)
            self.assertEqual(response.status_code, 201, response.data)
        # V3 no tiene participaciones: el staff no necesita participar en la vivienda.
        response = cliente(self.e.u_staff).post(f'/api/viviendas/{self.e.v3.pk}/participaciones/', {
            'persona': self.e.carla.pk, 'rol': 'ARRENDATARIO',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            set(ParticipacionVivienda.objects.values_list('persona__codigo', 'vivienda__identificador', 'rol')),
            {('P-DIEGO', 'Casa 1', 'PROPIETARIO_ADMIN'), ('P-CARLA', 'Casa 1', 'ARRENDATARIO'),
             ('P-SOFIA', 'Casa 1', 'CONVIVIENTE'), ('P-ANA', 'Casa 1', 'PROPIETARIO'),
             ('P-CARLA', 'Depto 101', 'ARRENDATARIO')},
        )

    def test_staff_tambien_respeta_duplicados_y_roles_validos(self):
        self.antes = ParticipacionVivienda.objects.count()
        self.assertRechazo(self.asignar(self.e.u_staff, self.e.carla, 'CONVIVIENTE'), 400)
        self.assertRechazo(self.asignar(self.e.u_staff, self.e.sofia, 'VECINO'), 400)
        self.assertEqual(ParticipacionVivienda.objects.get(persona=self.e.carla, vivienda=self.e.v1).rol,
                         'ARRENDATARIO')

    def test_ver_participaciones_requiere_participar(self):
        self.assertEqual(cliente(self.e.u_ana).get(self.url).status_code, 403)
        self.assertEqual(cliente(self.e.u_staff).get(self.url).status_code, 200)
