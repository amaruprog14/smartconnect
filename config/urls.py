from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from personas.views import PersonaViewSet
from terrenos.views import TerrenoViewSet
from viviendas.views import ViviendaViewSet
from accesos.views import PuntoAccesoViewSet

router = DefaultRouter()
router.register('personas', PersonaViewSet, basename='persona')
router.register('terrenos', TerrenoViewSet, basename='terreno')
router.register('viviendas', ViviendaViewSet, basename='vivienda')
router.register('puntos-acceso', PuntoAccesoViewSet, basename='punto-acceso')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
