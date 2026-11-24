from django.contrib import admin
from .models import ParticipacionVivienda, Vivienda

@admin.register(Vivienda)
class ViviendaAdmin(admin.ModelAdmin):
    list_display = ['identificador', 'tipo', 'terreno']
    list_filter = ['tipo', 'terreno']


@admin.register(ParticipacionVivienda)
class ParticipacionViviendaAdmin(admin.ModelAdmin):
    list_display = ['persona', 'vivienda', 'rol', 'activa']
    list_filter = ['rol', 'activa']
