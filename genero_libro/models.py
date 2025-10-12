from django.db import models
from base.models import Base

# Create your models here.
class Genero_libro(Base):
   genero=models.CharField(max_length=50)