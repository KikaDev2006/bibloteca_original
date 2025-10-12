from django.db import models
from base.models import Base

class Acciones_usuario(Base):
   usuario=models.ForeignKey("usuario.Usuario", on_delete=models.CASCADE)
   libro=models.ForeignKey("libro.Libro", on_delete=models.CASCADE)
   es_favorito=models.BooleanField(default=False)
   ultima_pagina_leida=models.ForeignKey("pagina.Pagina", on_delete=models.SET_NULL, null=True, blank=True, related_name='acciones_usuario')
   pendiente_leer=models.BooleanField(default=False)
   calificacion=models.IntegerField(default=0)
   


