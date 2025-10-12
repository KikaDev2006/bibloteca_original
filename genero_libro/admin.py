from django.contrib import admin
from .models import Genero_libro


@admin.register(Genero_libro)
class GeneroLibroAdmin(admin.ModelAdmin):
    list_display = ('id', 'genero', 'created_at', 'updated_at')
    search_fields = ('genero',)
    list_filter = ('created_at', 'updated_at')
    ordering = ('id',)
