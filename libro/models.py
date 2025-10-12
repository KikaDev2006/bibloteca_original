from django.db import models
from base.models import Base
from genero_libro.models import Genero_libro
from usuario.models import Usuario

# Create your models here.
class Libro(Base):
    nombre=models.CharField(max_length=100)
    version=models.IntegerField()
    genero=models.ForeignKey(Genero_libro, on_delete=models.PROTECT,null=True)
    color_portada=models.CharField(max_length=20,default="sin color")
    imagen_portada=models.ImageField(upload_to='libros/portadas', null=True, blank=True)
    usuario=models.ForeignKey(Usuario, on_delete=models.PROTECT)
    es_publico=models.BooleanField(default=True)