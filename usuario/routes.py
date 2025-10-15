from typing import List
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core import signing
from ninja import Router

from .models import Usuario
from .schemas import UsuarioIn, UsuarioOut, UsuarioUpdate, LoginIn, LoginOut, SuperUsuarioIn
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



@router.post("/crear-superusuario", response={200: dict, 403: dict})
def crear_superusuario(request, payload: SuperUsuarioIn):
    """
    Crea un superusuario solo si no existe ninguno en el sistema.
    """
    print(f"🔍 DEBUG: Método recibido: {request.method}")
    print(f"🔍 DEBUG: Path: {request.path}")
    print(f"🔍 DEBUG: Payload: {payload}")

    # Verificar si ya existe un superusuario
    if User.objects.filter(is_superuser=True).exists():
        print("🔍 DEBUG: Ya existe un superusuario")
        return 403, {
            "success": False,
            "message": "Ya existe un superusuario en el sistema"
        }

    # Crear el superusuario
    try:
        print(f"🔍 DEBUG: Creando superusuario para {payload.email}")
        superusuario = User.objects.create_user(
            username=payload.email,  # Usamos email como username
            email=payload.email,
            password=payload.contraseña,
            first_name=payload.nombre_completo.split()[0] if payload.nombre_completo else "",
            last_name=" ".join(payload.nombre_completo.split()[1:]) if len(payload.nombre_completo.split()) > 1 else ""
        )
        superusuario.is_superuser = True
        superusuario.is_staff = True
        superusuario.save()

        print(f"🔍 DEBUG: Superusuario creado exitosamente: {superusuario.username}")
        return 200, {
            "success": True,
            "message": f"Superusuario {superusuario.username} creado exitosamente",
            "usuario": {
                "id": superusuario.id,
                "username": superusuario.username,
                "email": superusuario.email,
                "is_superuser": superusuario.is_superuser,
                "is_staff": superusuario.is_staff
            }
        }
    except Exception as e:
        print(f"🔍 DEBUG: Error al crear superusuario: {str(e)}")
        return 200, {
            "success": False,
            "message": f"Error al crear superusuario: {str(e)}"
        }
