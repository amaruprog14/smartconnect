from django.contrib import admin
from .models import Vivienda

@admin.register(Vivienda)
class ViviendaAdmin(admin.ModelAdmin):
    list_display = ['identificador', 'tipo', 'terreno']
    list_filter = ['tipo', 'terreno']
