from datetime import datetime
from ninja import Schema


class UsuarioIn(Schema):
    nombre_completo: str
    email: str
    contraseña: str


class UsuarioOut(Schema):
    id: int
    nombre_completo: str
    email: str
    created_at: datetime
    updated_at: datetime


class UsuarioUpdate(Schema):
    nombre_completo: str = None
    email: str = None
    contraseña: str = None


class SuperUsuarioIn(Schema):
    nombre_completo: str
    email: str
    contraseña: str


class LoginIn(Schema):
    email: str
    contraseña: str


class LoginOut(Schema):
    success: bool
    usuario: UsuarioOut
    message: str
    token: str
