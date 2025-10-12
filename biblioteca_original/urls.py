from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from libro.routes import router as libro_router
from pagina.routes import router as pagina_router
from genero_libro.routes import router as genero_libro_router
from usuario.routes import router as usuario_router
from acciones_usuario.routes import router as acciones_usuario_router
biblioteca = NinjaAPI()

biblioteca.add_router("libro", libro_router)
biblioteca.add_router("genero_libro", genero_libro_router)
biblioteca.add_router("pagina", pagina_router)
biblioteca.add_router("usuario", usuario_router)
biblioteca.add_router("acciones_usuario", acciones_usuario_router)





urlpatterns = [
    path("", biblioteca.urls),
    path("admin/", admin.site.urls),
   
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
