from django.contrib import admin
from .models import PuntoAcceso

@admin.register(PuntoAcceso)
class PuntoAccesoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'terreno', 'vivienda', 'activo']
    list_filter = ['tipo', 'activo', 'terreno']
