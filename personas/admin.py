from django.contrib import admin
from .models import Persona

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombres', 'apellidos', 'email', 'usuario']
    search_fields = ['codigo', 'nombres', 'apellidos', 'email', 'usuario__username']
    # Selector con búsqueda para vincular la cuenta de usuario.
    autocomplete_fields = ['usuario']
