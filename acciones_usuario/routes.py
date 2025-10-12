from typing import List
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from ninja import Router

from .models import Acciones_usuario
from libro.models import Libro
from usuario.auth import token_auth
from .schemas import AccionUsuarioIn, AccionUsuarioUpdate, AccionUsuarioOut


router = Router(tags=["acciones_usuario"])


@router.get("/", response=List[AccionUsuarioOut], auth=token_auth)
def list_acciones_usuario(request):
    """Obtiene todas las acciones del usuario autenticado"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    acciones = (
        Acciones_usuario.objects
        .select_related("libro")
        .filter(usuario_id=usuario_id)
        .order_by("-updated_at")
    )
    
    return [
        AccionUsuarioOut(
            id=accion.id,
            usuario_id=accion.usuario_id,
            libro_id=accion.libro_id,
            libro_nombre=accion.libro.nombre,
            es_favorito=accion.es_favorito,
            ultima_pagina_leida=accion.ultima_pagina_leida,
            pendiente_leer=accion.pendiente_leer,
            calificacion=accion.calificacion,
            created_at=accion.created_at,
            updated_at=accion.updated_at,
        )
        for accion in acciones
    ]




@router.get("/libro/{libro_id}", response=AccionUsuarioOut, auth=token_auth)
def get_accion_by_libro(request, libro_id: int):
    """Obtiene la acción del usuario para un libro específico"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    # Verificar que el libro existe
    get_object_or_404(Libro, id=libro_id)
    
    accion = get_object_or_404(
        Acciones_usuario.objects.select_related("libro"),
        usuario_id=usuario_id,
        libro_id=libro_id
    )
    
    return AccionUsuarioOut(
        id=accion.id,
        usuario_id=accion.usuario_id,
        libro_id=accion.libro_id,
        libro_nombre=accion.libro.nombre,
        es_favorito=accion.es_favorito,
        ultima_pagina_leida=accion.ultima_pagina_leida,
        pendiente_leer=accion.pendiente_leer,
        calificacion=accion.calificacion,
        created_at=accion.created_at,
        updated_at=accion.updated_at,
    )


@router.post("/", response=AccionUsuarioOut, auth=token_auth)
def create_accion_usuario(request, payload: AccionUsuarioIn):
    """Crea una nueva acción de usuario para un libro"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    # Verificar que el libro existe
    libro = get_object_or_404(Libro, id=payload.libro_id)
    
    # Verificar si ya existe una acción para este usuario y libro
    if Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=payload.libro_id).exists():
        return HttpResponse("Ya existe una acción para este libro", status=400)
    
    accion = Acciones_usuario.objects.create(
        usuario_id=usuario_id,
        libro_id=payload.libro_id,
        es_favorito=payload.es_favorito,
        ultima_pagina_leida=payload.ultima_pagina_leida,
        pendiente_leer=payload.pendiente_leer,
        calificacion=payload.calificacion,
    )
    
    accion.refresh_from_db()
    
    return AccionUsuarioOut(
        id=accion.id,
        usuario_id=accion.usuario_id,
        libro_id=accion.libro_id,
        libro_nombre=libro.nombre,
        es_favorito=accion.es_favorito,
        ultima_pagina_leida=accion.ultima_pagina_leida,
        pendiente_leer=accion.pendiente_leer,
        calificacion=accion.calificacion,
        created_at=accion.created_at,
        updated_at=accion.updated_at,
    )

@router.put("/libro/{libro_id}", response=AccionUsuarioOut, auth=token_auth)
def update_accion_by_libro(request, libro_id: int, payload: AccionUsuarioUpdate):
    """Actualiza la acción del usuario para un libro específico"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    # Verificar que el libro existe
    libro = get_object_or_404(Libro, id=libro_id)
    
    accion = get_object_or_404(
        Acciones_usuario,
        usuario_id=usuario_id,
        libro_id=libro_id
    )
    
    # Actualizar solo los campos proporcionados
    if payload.es_favorito is not None:
        accion.es_favorito = payload.es_favorito
    if payload.ultima_pagina_leida is not None:
        accion.ultima_pagina_leida = payload.ultima_pagina_leida
    if payload.pendiente_leer is not None:
        accion.pendiente_leer = payload.pendiente_leer
    if payload.calificacion is not None:
        accion.calificacion = payload.calificacion
    
    accion.save()
    
    return AccionUsuarioOut(
        id=accion.id,
        usuario_id=accion.usuario_id,
        libro_id=accion.libro_id,
        libro_nombre=libro.nombre,
        es_favorito=accion.es_favorito,
        ultima_pagina_leida=accion.ultima_pagina_leida,
        pendiente_leer=accion.pendiente_leer,
        calificacion=accion.calificacion,
        created_at=accion.created_at,
        updated_at=accion.updated_at,
    )


@router.delete("/{accion_id}", auth=token_auth)
def delete_accion_usuario(request, accion_id: int):
    """Elimina una acción de usuario"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    accion = get_object_or_404(Acciones_usuario, id=accion_id)
    
    # Verificar que el usuario es propietario de la acción
    if accion.usuario_id != usuario_id:
        return HttpResponse("No tienes permisos para realizar esta acción", status=403)
    
    accion.delete()
    return {"success": True}
