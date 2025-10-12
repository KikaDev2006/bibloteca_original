from django.db import models
from base.models import Base

class Usuario(Base):
    nombre_completo=models.CharField(max_length=300)
    email=models.EmailField(unique=True)
    contraseña=models.CharField(max_length=100)
   


