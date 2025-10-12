from typing import List
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from ninja import Router
from functools import wraps

from .models import Pagina
from libro.models import Libro
from usuario.auth import token_auth
from .schemas import PaginaIn, PaginaOut


router = Router(tags=["paginas"])


def require_book_ownership(func):
    """Decorador para verificar que el usuario es propietario del libro de la página"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # request.auth contiene {'uid': ..., 'email': ...} del token
        usuario_id = request.auth.get('uid')
        if not usuario_id:
            return HttpResponse("No autenticado", status=401)
        
        # Obtener pagina_id y libro_id de kwargs
        pagina_id = kwargs.get('pagina_id')
        libro_id = kwargs.get('libro_id')
        
        # Si tenemos pagina_id, verificar a través de la página
        if pagina_id:
            pagina = get_object_or_404(Pagina.objects.select_related("libro"), id=pagina_id)
            if pagina.libro.usuario_id != usuario_id:
                return HttpResponse("No tienes permisos para gestionar páginas de este libro", status=403)
        
        # Si tenemos libro_id, verificar directamente el libro
        elif libro_id:
            libro = get_object_or_404(Libro, id=libro_id)
            if libro.usuario_id != usuario_id:
                return HttpResponse("No tienes permisos para gestionar páginas de este libro", status=403)
        
        return func(request, *args, **kwargs)
    return wrapper


@router.get("/", response=List[PaginaOut])
def list_paginas(request):
    paginas = Pagina.objects.select_related("libro").all().order_by("id")
    return [
        PaginaOut(
            id=p.id,
            contenido=p.contenido,
            tipo=p.tipo,
            titulo=p.titulo,
            libro_id=p.libro_id,
            libro_nombre=(p.libro.nombre if p.libro_id else None),
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in paginas
    ]


@router.get("/{pagina_id}", response=PaginaOut)
def get_pagina(request, pagina_id: int):
    p = get_object_or_404(Pagina.objects.select_related("libro"), id=pagina_id)
    return PaginaOut(
        id=p.id,
        contenido=p.contenido,
        tipo=p.tipo,
        titulo=p.titulo,
        libro_id=p.libro_id,
        libro_nombre=(p.libro.nombre if p.libro_id else None),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post("/", response=PaginaOut, auth=token_auth)
def create_pagina(request, payload: PaginaIn):
    # Extraer usuario_id del token
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    # Verificar que el usuario es propietario del libro
    libro = get_object_or_404(Libro, id=payload.libro_id)
    if libro.usuario_id != usuario_id:
        return HttpResponse("No tienes permisos para agregar páginas a este libro", status=403)
    
    p = Pagina.objects.create(
        contenido=payload.contenido,
        tipo=payload.tipo,
        titulo=payload.titulo,
        libro_id=payload.libro_id,
    )
    p = Pagina.objects.select_related("libro").get(id=p.id)
    return PaginaOut(
        id=p.id,
        contenido=p.contenido,
        tipo=p.tipo,
        titulo=p.titulo,
        libro_id=p.libro_id,
        libro_nombre=(p.libro.nombre if p.libro_id else None),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.put("/{pagina_id}", response=PaginaOut, auth=token_auth)
@require_book_ownership
def update_pagina(request, pagina_id: int, payload: PaginaIn):
    p = get_object_or_404(Pagina, id=pagina_id)
    p.contenido = payload.contenido
    p.tipo = payload.tipo
    p.titulo = payload.titulo
    p.libro_id = payload.libro_id
    p.save()
    p = Pagina.objects.select_related("libro").get(id=p.id)
    return PaginaOut(
        id=p.id,
        contenido=p.contenido,
        tipo=p.tipo,
        titulo=p.titulo,
        libro_id=p.libro_id,
        libro_nombre=(p.libro.nombre if p.libro_id else None),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.delete("/{pagina_id}", auth=token_auth)
@require_book_ownership
def delete_pagina(request, pagina_id: int):
    p = get_object_or_404(Pagina, id=pagina_id)
    p.delete()
    return {"success": True}

