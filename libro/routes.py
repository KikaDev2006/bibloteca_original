from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from django.db.models import Avg, Q
from ninja import Router, File, Form
from ninja.files import UploadedFile
from functools import wraps
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Libro
from pagina.models import Pagina
from usuario.models import Usuario
from usuario.auth import token_auth
from .schemas import LibroIn, LibroOut
from acciones_usuario.models import Acciones_usuario


router = Router(tags=["libros"])


def calcular_calificacion_promedio(libro_id: int) -> Optional[float]:
    """Calcula la calificación promedio de un libro excluyendo calificaciones de 0"""
    resultado = Acciones_usuario.objects.filter(
        libro_id=libro_id,
        calificacion__gt=0  # Solo calificaciones mayores a 0
    ).aggregate(promedio=Avg('calificacion'))
    
    return round(resultado['promedio'], 2) if resultado['promedio'] is not None else None


def obtener_numero_pagina_por_id(libro_id: int, pagina_id: int) -> Optional[int]:
    """Obtiene el número de página (posición) dado su ID"""
    if not pagina_id:
        return None
    
    paginas = list(Pagina.objects.filter(libro_id=libro_id).order_by('id').values_list('id', flat=True))
    
    try:
        # El número de página es 1-indexed
        return paginas.index(pagina_id) + 1
    except ValueError:
        return None


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
            ultima_pagina_leida_id = None
            esta_terminado = None
            total_paginas = None
            
            es_favorito = None
            pendiente_leer = None
            
            if usuario_id:
                accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
                if accion:
                    ultima_pagina_leida_id = accion.ultima_pagina_leida_id
                    ultima_pagina_leida = obtener_numero_pagina_por_id(libro.id, accion.ultima_pagina_leida_id) if accion.ultima_pagina_leida_id else None
                    total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
                    esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 and ultima_pagina_leida else False
                    es_favorito = accion.es_favorito
                    pendiente_leer = accion.pendiente_leer
            
            # Calcular calificación promedio
            calificacion_promedio = calcular_calificacion_promedio(libro.id)
            
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
                    ultima_pagina_leida_id=ultima_pagina_leida_id,
                    esta_terminado=esta_terminado,
                    total_paginas=total_paginas,
                    es_favorito=es_favorito,
                    pendiente_leer=pendiente_leer,
                    calificacion_promedio=calificacion_promedio,
                )
            )
    return result


@router.get("/todos-autenticado", response=List[LibroOut], auth=token_auth)
def list_libros_autenticado(request):
    """Obtiene todos los libros públicos con las acciones del usuario autenticado"""
    usuario_id = request.auth.get('uid')
    if not usuario_id:
        return HttpResponse("No autenticado", status=401)
    
    libros = (
        Libro.objects.select_related("genero", "usuario")
        .filter(es_publico=True)
        .order_by("id")
    )
    
    result = []
    for libro in libros:
        # Obtener información de acciones de usuario
        accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
        ultima_pagina_leida = None
        ultima_pagina_leida_id = None
        esta_terminado = None
        total_paginas = None
        es_favorito = None
        pendiente_leer = None
        
        if accion:
            ultima_pagina_leida_id = accion.ultima_pagina_leida_id
            ultima_pagina_leida = obtener_numero_pagina_por_id(libro.id, accion.ultima_pagina_leida_id) if accion.ultima_pagina_leida_id else None
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 and ultima_pagina_leida else False
            es_favorito = accion.es_favorito
            pendiente_leer = accion.pendiente_leer
        
        # Calcular calificación promedio
        calificacion_promedio = calcular_calificacion_promedio(libro.id)
        
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
                ultima_pagina_leida_id=ultima_pagina_leida_id,
                esta_terminado=esta_terminado,
                total_paginas=total_paginas,
                es_favorito=es_favorito,
                pendiente_leer=pendiente_leer,
                calificacion_promedio=calificacion_promedio,
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
        ultima_pagina_leida_id = None
        esta_terminado = None
        total_paginas = None
        
        es_favorito = None
        pendiente_leer = None
        
        if accion:
            ultima_pagina_leida_id = accion.ultima_pagina_leida_id
            ultima_pagina_leida = obtener_numero_pagina_por_id(libro.id, accion.ultima_pagina_leida_id) if accion.ultima_pagina_leida_id else None
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 and ultima_pagina_leida else False
            es_favorito = accion.es_favorito
            pendiente_leer = accion.pendiente_leer
        
        # Calcular calificación promedio
        calificacion_promedio = calcular_calificacion_promedio(libro.id)
        
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
                ultima_pagina_leida_id=ultima_pagina_leida_id,
                esta_terminado=esta_terminado,
                total_paginas=total_paginas,
                es_favorito=es_favorito,
                pendiente_leer=pendiente_leer,
                calificacion_promedio=calificacion_promedio,
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
    ultima_pagina_leida_id = None
    esta_terminado = None
    total_paginas = None
    
    es_favorito = None
    pendiente_leer = None
    
    if usuario_id:
        accion = Acciones_usuario.objects.filter(usuario_id=usuario_id, libro_id=libro.id).first()
        if accion:
            ultima_pagina_leida_id = accion.ultima_pagina_leida_id
            ultima_pagina_leida = obtener_numero_pagina_por_id(libro.id, accion.ultima_pagina_leida_id) if accion.ultima_pagina_leida_id else None
            total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
            esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 and ultima_pagina_leida else False
            es_favorito = accion.es_favorito
            pendiente_leer = accion.pendiente_leer
    
    # Calcular calificación promedio
    calificacion_promedio = calcular_calificacion_promedio(libro.id)
    
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
        ultima_pagina_leida_id=ultima_pagina_leida_id,
        esta_terminado=esta_terminado,
        total_paginas=total_paginas,
        es_favorito=es_favorito,
        pendiente_leer=pendiente_leer,
        calificacion_promedio=calificacion_promedio,
    )
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
            ultima_pagina_leida_id = accion.ultima_pagina_leida_id
            ultima_pagina_leida = obtener_numero_pagina_por_id(libro.id, accion.ultima_pagina_leida_id) if accion.ultima_pagina_leida_id else None
            esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 and ultima_pagina_leida else False
            calificacion_promedio = calcular_calificacion_promedio(libro.id)
            
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
                    ultima_pagina_leida_id=ultima_pagina_leida_id,
                    esta_terminado=esta_terminado,
                    total_paginas=total_paginas,
                    es_favorito=accion.es_favorito,
                    pendiente_leer=accion.pendiente_leer,
                    calificacion_promedio=calificacion_promedio,
                )
            )
    return result


@router.get("/{libro_id}/download_pdf")
def download_libro_pdf(request, libro_id: int):
    """Descarga el libro como PDF, con cada página del libro como una página separada en el PDF"""
    libro = get_object_or_404(Libro.objects.select_related("usuario"), id=libro_id)
    
    # Verificar permisos: solo mostrar si es público o si el usuario es el autor
    usuario_id = None
    if hasattr(request, 'auth') and request.auth:
        usuario_id = request.auth.get('uid')
    
    if not libro.es_publico and (not usuario_id or libro.usuario_id != usuario_id):
        return HttpResponse("No tienes permisos para descargar este libro", status=403)
    
    # Obtener páginas del libro
    paginas = Pagina.objects.filter(libro_id=libro_id).order_by('id')
    
    # Generar PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750  # Posición inicial en la página
    
    # Título del libro en la primera página
    p.drawString(100, y, f"Libro: {libro.nombre}")
    y -= 30
    p.drawString(100, y, f"Autor: {libro.usuario.nombre_completo}")
    y -= 30
    
    for pagina in paginas:
        # Agregar espacio antes de la nueva página del libro
        if y < 100:  # Si queda poco espacio, pasar a nueva página del PDF
            p.showPage()
            y = 750
        
        # Título de la página
        if pagina.titulo:
            p.drawString(100, y, f"Página: {pagina.titulo}")
            y -= 20
        
        # Contenido de la página
        lines = pagina.contenido.split('\n')
        for line in lines:
            if y < 50:  # Nueva página del PDF si no hay espacio
                p.showPage()
                y = 750
            p.drawString(100, y, line)
            y -= 15
        
        # Finalizar la página del PDF después de cada página del libro
        p.showPage()
        y = 750  # Reiniciar posición para la siguiente página del PDF
    
    p.save()
    buffer.seek(0)
    
    # Crear respuesta HTTP con el PDF
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{libro.nombre}.pdf"'
    return response


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
    ultima_pagina_leida_id = None
    esta_terminado = None
    total_paginas = None
    es_favorito = None
    pendiente_leer = None
    
    if accion:
        ultima_pagina_leida = accion.ultima_pagina_leida
        ultima_pagina_leida_id = obtener_pagina_id_por_numero(libro.id, accion.ultima_pagina_leida)
        total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
        esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
        es_favorito = accion.es_favorito
        pendiente_leer = accion.pendiente_leer
    
    # Calcular calificación promedio
    calificacion_promedio = calcular_calificacion_promedio(libro.id)
    
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
        ultima_pagina_leida_id=ultima_pagina_leida_id,
        esta_terminado=esta_terminado,
        total_paginas=total_paginas,
        es_favorito=es_favorito,
        pendiente_leer=pendiente_leer,
        calificacion_promedio=calificacion_promedio,
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
    ultima_pagina_leida_id = None
    esta_terminado = None
    total_paginas = None
    es_favorito = None
    pendiente_leer = None
    
    if accion:
        ultima_pagina_leida = accion.ultima_pagina_leida
        ultima_pagina_leida_id = obtener_pagina_id_por_numero(libro.id, accion.ultima_pagina_leida)
        total_paginas = Pagina.objects.filter(libro_id=libro.id).count()
        esta_terminado = ultima_pagina_leida >= total_paginas if total_paginas > 0 else False
        es_favorito = accion.es_favorito
        pendiente_leer = accion.pendiente_leer
    
    # Calcular calificación promedio
    calificacion_promedio = calcular_calificacion_promedio(libro.id)
    
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
        ultima_pagina_leida_id=ultima_pagina_leida_id,
        esta_terminado=esta_terminado,
        total_paginas=total_paginas,
        es_favorito=es_favorito,
        pendiente_leer=pendiente_leer,
        calificacion_promedio=calificacion_promedio,
    )


@router.delete("/{libro_id}", auth=token_auth)
@require_ownership
def delete_libro(request, libro_id: int):
    libro = get_object_or_404(Libro, id=libro_id)
    libro.delete()
    return {"success": True}


