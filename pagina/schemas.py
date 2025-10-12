from datetime import datetime
from typing import Optional
from ninja import Schema


class PaginaIn(Schema):
    contenido: str
    tipo: str
    titulo: Optional[str] = None
    libro_id: int


class PaginaOut(Schema):
    id: int
    contenido: str
    tipo: str
    titulo: Optional[str]
    libro_id: int
    libro_nombre: Optional[str]
    created_at: datetime
    updated_at: datetime

