from django.core import signing
from django.http import HttpRequest
from ninja.security import HttpBearer


class TokenAuth(HttpBearer):
    """
    Autenticación basada en token Bearer.
    El cliente debe enviar: Authorization: Bearer <token>
    """
    
    def authenticate(self, request: HttpRequest, token: str):
        try:
            # Verificar y decodificar el token
            payload = signing.loads(token, salt='usuario.auth', max_age=86400)  # 24 horas
            # Retornar el payload (uid, email) para que esté disponible en request.auth
            return payload
        except signing.SignatureExpired:
            return None  # Token expirado
        except signing.BadSignature:
            return None  # Token inválido
        except Exception:
            return None  # Cualquier otro error


# Instancia global para usar en las rutas
token_auth = TokenAuth()
