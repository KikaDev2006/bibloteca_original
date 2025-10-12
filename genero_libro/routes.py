from typing import List
from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Genero_libro
from .schemas import GeneroLibroIn, GeneroLibroOut


router = Router(tags=["generos"])


@router.get("/", response=List[GeneroLibroOut])
def list_generos(request):
    generos = Genero_libro.objects.all().order_by("id")
    return [
        GeneroLibroOut(
            id=g.id,
            genero=g.genero,
            created_at=g.created_at,
            updated_at=g.updated_at,
        )
        for g in generos
    ]


@router.get("/{genero_id}", response=GeneroLibroOut)
def get_genero(request, genero_id: int):
    g = get_object_or_404(Genero_libro, id=genero_id)
    return GeneroLibroOut(
        id=g.id,
        genero=g.genero,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )

