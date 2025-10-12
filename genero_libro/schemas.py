from datetime import datetime
from ninja import Schema


class GeneroLibroIn(Schema):
    genero: str


class GeneroLibroOut(Schema):
    id: int
    genero: str
    created_at: datetime
    updated_at: datetime

