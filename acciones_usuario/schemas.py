from datetime import datetime
from typing import Optional
from ninja import Schema


class AccionUsuarioIn(Schema):
    libro_id: int
    es_favorito: Optional[bool] = False
    ultima_pagina_leida: Optional[int] = 0
    pendiente_leer: Optional[bool] = False
    calificacion: Optional[int] = 0


class AccionUsuarioUpdate(Schema):
    es_favorito: Optional[bool] = None
    ultima_pagina_leida: Optional[int] = None
    pendiente_leer: Optional[bool] = None
    calificacion: Optional[int] = None


class AccionUsuarioOut(Schema):
    id: int
    usuario_id: int
    libro_id: int
    libro_nombre: Optional[str]
    es_favorito: bool
    ultima_pagina_leida: int
    pendiente_leer: bool
    calificacion: int
    created_at: datetime
    updated_at: datetime
