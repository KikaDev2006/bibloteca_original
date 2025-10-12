from django.db import models
from base.models import Base
from libro.models import Libro
# Create your models here.
class Pagina(Base):
    contenido=models.TextField()
    tipo=models.CharField(max_length=100)
    titulo=models.CharField(max_length=200, null=True)
    libro=models.ForeignKey(Libro, on_delete=models.CASCADE)
    