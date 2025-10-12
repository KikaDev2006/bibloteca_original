from django.db import models
from base.models import Base

class Acciones_usuario(Base):
   usuario=models.ForeignKey("usuario.Usuario", on_delete=models.CASCADE)
   libro=models.ForeignKey("libro.Libro", on_delete=models.CASCADE)
   es_favorito=models.BooleanField(default=False)
   ultima_pagina_leida=models.IntegerField(default=0)
   pendiente_leer=models.BooleanField(default=False)
   calificacion=models.IntegerField(default=0)
   


