from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from ninja import Router, File, Form
from ninja.files import UploadedFile
from functools import wraps

from .models import Libro
from pagina.models import Pagina
from usuario.models import Usuario
from usuario.auth import token_auth
from .schemas import LibroIn, LibroOut
from acciones_usuario.models import Acciones_usuario


router = Router(tags=["libros"])


def require_ownership(func):
    """Decorador para verificar que el usuario es propietario del libro"""
    @wraps(func)
    def wrapper(request, libro_id: int, *args, **kwargs):
        # request.auth contiene {'uid': ..., 'email': ...} del token
        usuario_id = request.auth.get('uid')
        if not usuario_id:
            return HttpResponse("No autenticado", status=401)
        
        libro = get_object_or_404(Libro, id=libro_id)
        if libro.usuario_id != usuario_id:
            return HttpResponse("No tienes permisos para realizar esta acción", status=403)
        
        return func(request, libro_id, *args, **kwargs)
    return wrapper


@router.get("/", response=List[LibroOut])
def list_libros(request):
    # Obtener usuario_id del token si está autenticado
    usuario_id = None
    if hasattr(request, 'auth') and request.auth:
        usuario_id = request.auth.get('uid')
    
    libros = (
        Libro.objects.select_related("genero", "usuario")
        .all()
        .order_by("id")
    )
    
    # Filtrar libros según privacidad
    result = []
    for libro in libros:
        # Mostrar si es público O si el usuario es el autor
        if libro.es_publico or (usuario_id and libro.usuario_id == usuario_id):
            # Obtener información de acciones de usuario si está autenticado
            ultima_pagina_leida = None
            esta_terminado = None
            total_paginas = None
            
            es_favorito = None
            pendiente_leer = None
            
            if usuario_id:
                accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
                if accion:
                    ultima_pagina_leida = accion.ultima_pagina_leida
                    total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
                    esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
                    es_favorito = accion.es_favorito
                    pendiente_leer = accion.pendiente_leer
            
            result.append(
                LibroOut(
                    id=libro.id,
                    nombre=libro.nombre,
                    version=libro.version,
                    genero_id=libro.genero_id,
                    genero=(libro.genero.genero if libro.genero_id else None),
                    color_portada=libro.color_portada,
                    imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
                    es_publico=libro.es_publico,
                    usuario_id=libro.usuario_id,
                    autor=libro.usuario.nombre_completo,
                    created_at=libro.created_at,
                    updated_at=libro.updated_at,
                    ultima_pagina_leida=ultima_pagina_leida,
                    esta_terminado=esta_terminado,
                    total_paginas=total_paginas,
                    es_favorito=es_favorito,
                    pendiente_leer=pendiente_leer,
                )
            )
    return result


@router.get("/mis-libros", response=List[LibroOut], auth=token_auth)
def mis_libros(request):
    """Obtiene todos los libros del usuario autenticado (públicos y privados)"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    libros = (
        Libro.objects.select_related("genero", "usuario")
        .filter(usuario_id=usuario_id)
        .order_by("-created_at")
    )
    
    result = []
    for libro in libros:
        # Obtener información de acciones de usuario
        accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
        ultima_pagina_leida = None
        esta_terminado = None
        total_paginas = None
        
        es_favorito = None
        pendiente_leer = None
        
        if accion:
            ultima_pagina_leida = accion.ultima_pagina_leida
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
            es_favorito = accion.es_favorito
            pendiente_leer = accion.pendiente_leer
        
        result.append(
            LibroOut(
                id=libro.id,
                nombre=libro.nombre,
                version=libro.version,
                genero_id=libro.genero_id,
                genero=(libro.genero.genero if libro.genero_id else None),
                color_portada=libro.color_portada,
                imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
                es_publico=libro.es_publico,
                usuario_id=libro.usuario_id,
                autor=libro.usuario.nombre_completo,
                created_at=libro.created_at,
                updated_at=libro.updated_at,
                ultima_pagina_leida=ultima_pagina_leida,
                esta_terminado=esta_terminado,
                total_paginas=total_paginas,
                es_favorito=es_favorito,
                pendiente_leer=pendiente_leer,
            )
        )
    return result


@router.get("/{libro_id}", response=LibroOut)
def get_libro(request, libro_id: int):
    libro = get_object_or_404(Libro.objects.select_related("genero", "usuario"), id=libro_id)
    
    # Verificar privacidad: solo mostrar si es público O si el usuario es el autor
    usuario_id = None
    if hasattr(request, 'auth') and request.auth:
        usuario_id = request.auth.get('uid')
    
    if not libro.es_publico:
        if not usuario_id or libro.usuario_id != usuario_id:
            return HttpResponse("Este libro es privado", status=403)
    
    # Obtener información de acciones de usuario si está autenticado
    ultima_pagina_leida = None
    esta_terminado = None
    total_paginas = None
    
    es_favorito = None
    pendiente_leer = None
    
    if usuario_id:
        accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
        if accion:
            ultima_pagina_leida = accion.ultima_pagina_leida
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
            es_favorito = accion.es_favorito
            pendiente_leer = accion.pendiente_leer
    
    return LibroOut(
        id=libro.id,
        nombre=libro.nombre,
        version=libro.version,
        genero_id=libro.genero_id,
        genero=(libro.genero.genero if libro.genero_id else None),
        color_portada=libro.color_portada,
        imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
        es_publico=libro.es_publico,
        usuario_id=libro.usuario_id,
        autor=libro.usuario.nombre_completo,
        created_at=libro.created_at,
        updated_at=libro.updated_at,
        ultima_pagina_leida=ultima_pagina_leida,
        esta_terminado=esta_terminado,
        total_paginas=total_paginas,
        es_favorito=es_favorito,
        pendiente_leer=pendiente_leer,
    )


@router.post("/", response=LibroOut, auth=token_auth)
def create_libro(
    request,
    nombre: str = Form(...),
    version: int = Form(...),
    color_portada: str = Form(...),
    genero_id: Optional[int] = Form(None),
    es_publico: bool = Form(True),
    imagen_portada: Optional[UploadedFile] = File(None)
):
    # Extraer usuario_id del token
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    libro = Libro.objects.create(
        nombre=nombre,
        version=version,
        genero_id=genero_id,
        color_portada=color_portada,
        imagen_portada=imagen_portada,
        es_publico=es_publico,
        usuario_id=usuario_id,
    )
    libro.refresh_from_db()
    libro = Libro.objects.select_related("genero", "usuario").get(id=libro.id)
    
    # Obtener información de acciones de usuario
    accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
    ultima_pagina_leida = None
    esta_terminado = None
    total_paginas = None
    es_favorito = None
    pendiente_leer = None
    
    if accion:
        ultima_pagina_leida = accion.ultima_pagina_leida
        total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
        esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
        es_favorito = accion.es_favorito
        pendiente_leer = accion.pendiente_leer
    
    return LibroOut(
        id=libro.id,
        nombre=libro.nombre,
        version=libro.version,
        genero_id=libro.genero_id,
        genero=(libro.genero.genero if libro.genero_id else None),
        color_portada=libro.color_portada,
        imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
        es_publico=libro.es_publico,
        usuario_id=libro.usuario_id,
        autor=libro.usuario.nombre_completo,
        created_at=libro.created_at,
        updated_at=libro.updated_at,
        ultima_pagina_leida=ultima_pagina_leida,
        esta_terminado=esta_terminado,
        total_paginas=total_paginas,
        es_favorito=es_favorito,
        pendiente_leer=pendiente_leer,
    )


@router.put("/{libro_id}", response=LibroOut, auth=token_auth)
@require_ownership
def update_libro(
    request,
    libro_id: int,
    nombre: Optional[str] = Form(None),
    version: Optional[int] = Form(None),
    color_portada: Optional[str] = Form(None),
    genero_id: Optional[int] = Form(None),
    es_publico: Optional[bool] = Form(None),
    imagen_portada: Optional[UploadedFile] = File(None)
):
    libro = get_object_or_404(Libro, id=libro_id)
    if nombre is not None:
        libro.nombre = nombre
    if version is not None:
        libro.version = version
    if color_portada is not None:
        libro.color_portada = color_portada
    if genero_id is not None:
        libro.genero_id = genero_id
    if es_publico is not None:
        libro.es_publico = es_publico
    if imagen_portada:
        libro.imagen_portada = imagen_portada
    libro.save()
    libro = Libro.objects.select_related("genero", "usuario").get(id=libro.id)
    
    # Obtener información de acciones de usuario
    usuario_id = request.auth.get('uid')
    accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
    ultima_pagina_leida = None
    esta_terminado = None
    total_paginas = None
    es_favorito = None
    pendiente_leer = None
    
    if accion:
        ultima_pagina_leida = accion.ultima_pagina_leida
        total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
        esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
        es_favorito = accion.es_favorito
        pendiente_leer = accion.pendiente_leer
    
    return LibroOut(
        id=libro.id,
        nombre=libro.nombre,
        version=libro.version,
        genero_id=libro.genero_id,
        genero=(libro.genero.genero if libro.genero_id else None),
        color_portada=libro.color_portada,
        imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
        es_publico=libro.es_publico,
        usuario_id=libro.usuario_id,
        autor=libro.usuario.nombre_completo,
        created_at=libro.created_at,
        updated_at=libro.updated_at,
        ultima_pagina_leida=ultima_pagina_leida,
        esta_terminado=esta_terminado,
        total_paginas=total_paginas,
        es_favorito=es_favorito,
        pendiente_leer=pendiente_leer,
    )


@router.delete("/{libro_id}", auth=token_auth)
@require_ownership
def delete_libro(request, libro_id: int):
    libro = get_object_or_404(Libro, id=libro_id)
    libro.delete()
    return {"success": True}


@router.get("/{libro_id}/paginas")
def list_paginas_by_libro(request, libro_id: int):
    get_object_or_404(Libro, id=libro_id)
    paginas = Pagina.objects.filter(libro_id=libro_id).order_by("id")
    return [
        {
            "id": p.id,
            "contenido": p.contenido,
            "tipo": p.tipo,
            "titulo": p.titulo,
            "libro_id": p.libro_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        for p in paginas
    ]


@router.get("/favoritos/list", response=List[LibroOut], auth=token_auth)
def list_favoritos(request):
    """Obtiene todos los libros favoritos del usuario"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    # Obtener acciones de usuario donde es_favorito=True
    acciones = (
        Acciones_usuario.objects
        .select_related("libro", "libro__genero", "libro__usuario")
        .filter(usuario_id=usuario_id, es_favorito=True)
        .order_by("-updated_at")
    )
    
    result = []
    for accion in acciones:
        libro = accion.libro
        # Verificar que el libro es público o el usuario es el autor
        if libro.es_publico or libro.usuario_id == usuario_id:
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = accion.ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
            
            result.append(
                LibroOut(
                    id=libro.id,
                    nombre=libro.nombre,
                    version=libro.version,
                    genero_id=libro.genero_id,
                    genero=(libro.genero.genero if libro.genero_id else None),
                    color_portada=libro.color_portada,
                    imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
                    es_publico=libro.es_publico,
                    usuario_id=libro.usuario_id,
                    autor=libro.usuario.nombre_completo,
                    created_at=libro.created_at,
                    updated_at=libro.updated_at,
                    ultima_pagina_leida=accion.ultima_pagina_leida,
                    esta_terminado=esta_terminado,
                    total_paginas=total_paginas,
                    es_favorito=accion.es_favorito,
                    pendiente_leer=accion.pendiente_leer,
                )
            )
    return result


@router.get("/pendientes/list", response=List[LibroOut], auth=token_auth)
def list_pendientes(request):
    """Obtiene todos los libros pendientes de leer del usuario"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    # Obtener acciones de usuario donde pendiente_leer=True
    acciones = (
        Acciones_usuario.objects
        .select_related("libro", "libro__genero", "libro__usuario")
        .filter(usuario_id=usuario_id, pendiente_leer=True)
        .order_by("-updated_at")
    )
    
    result = []
    for accion in acciones:
        libro = accion.libro
        # Verificar que el libro es público o el usuario es el autor
        if libro.es_publico or libro.usuario_id == usuario_id:
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = accion.ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
            
            result.append(
                LibroOut(
                    id=libro.id,
                    nombre=libro.nombre,
                    version=libro.version,
                    genero_id=libro.genero_id,
                    genero=(libro.genero.genero if libro.genero_id else None),
                    color_portada=libro.color_portada,
                    imagen_portada=libro.imagen_portada.url if libro.imagen_portada else None,
                    es_publico=libro.es_publico,
                    usuario_id=libro.usuario_id,
                    autor=libro.usuario.nombre_completo,
                    created_at=libro.created_at,
                    updated_at=libro.updated_at,
                    ultima_pagina_leida=accion.ultima_pagina_leida,
                    esta_terminado=esta_terminado,
                    total_paginas=total_paginas,
                    es_favorito=accion.es_favorito,
                    pendiente_leer=accion.pendiente_leer,
                )
            )
    return result
