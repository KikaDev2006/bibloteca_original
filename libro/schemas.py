from datetime import datetime
from typing import Optional
from ninja import Schema, File
from ninja.files import UploadedFile


class LibroIn(Schema):
    nombre: str
    version: int
    genero_id: Optional[int] = None
    color_portada: str
    es_publico: bool = True


class LibroOut(Schema):
    id: int
    nombre: str
    version: int
    genero_id: Optional[int]
    genero: Optional[str]
    color_portada: str
    imagen_portada: Optional[str]
    es_publico: bool
    usuario_id: int
    autor: str
    created_at: datetime
    updated_at: datetime
    ultima_pagina_leida: Optional[int] = None
    ultima_pagina_leida_id: Optional[int] = None
    esta_terminado: Optional[bool] = None
    total_paginas: Optional[int] = None
    es_favorito: Optional[bool] = None
    pendiente_leer: Optional[bool] = None
    calificacion_promedio: Optional[float] = None
    

