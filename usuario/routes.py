from typing import List
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core import signing
from ninja import Router

from .models import Usuario
from .schemas import UsuarioIn, UsuarioOut, UsuarioUpdate, LoginIn, LoginOut
from .auth import token_auth


router = Router(tags=["usuarios"])

@router.get("/me", response=UsuarioOut, auth=token_auth)
def get_current_user(request):
    # request.auth contiene el payload del token: {'uid': ..., 'email': ...}
    usuario_id = request.auth.get('uid')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    return UsuarioOut(
        id=usuario.id,
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )

@router.post("/", response=UsuarioOut)
def create_usuario(request, payload: UsuarioIn):
    usuario = Usuario.objects.create(
        nombre_completo=payload.nombre_completo,
        email=payload.email,
        contraseña=payload.contraseña,
    )
    usuario.refresh_from_db()
    return UsuarioOut(
        id=usuario.id,
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )

# Rutas de autenticación
@router.post("/login", response=LoginOut)
def login(request, payload: LoginIn):
    try:
        usuario = Usuario.objects.get(email=payload.email, contraseña=payload.contraseña)
        
        # Generar token firmado (incluye id y email)
        token = signing.dumps({
            'uid': usuario.id,
            'email': usuario.email,
        }, salt='usuario.auth')
        
        return LoginOut(
            success=True,
            usuario=UsuarioOut(
                id=usuario.id,
                nombre_completo=usuario.nombre_completo,
                email=usuario.email,
                created_at=usuario.created_at,
                updated_at=usuario.updated_at,
            ),
            message="Login exitoso",
            token=token,
        )
    except Usuario.DoesNotExist:
        return HttpResponse("Credenciales incorrectas", status=401)

@router.post("/logout", auth=token_auth)
def logout(request):
    # Con tokens, el logout es del lado del cliente (eliminar el token)
    # Aquí solo confirmamos que el token es válido
    return {"success": True, "message": "Logout exitoso"}


@router.put("/{usuario_id}", response=UsuarioOut, auth=token_auth)
def update_usuario(request, usuario_id: int, payload: UsuarioUpdate):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Solo actualizar los campos que se proporcionan
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    usuario.save()
    usuario.refresh_from_db()
    
    return UsuarioOut(
        id=usuario.id,
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )


@router.delete("/{usuario_id}", auth=token_auth)
def delete_usuario(request, usuario_id: int):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    usuario.delete()
    return {"success": True}





