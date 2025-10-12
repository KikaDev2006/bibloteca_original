from django.apps import AppConfig


class BibliotecaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'biblioteca_original'

    def ready(self):
        # Ejecutar solo si no está deshabilitado
        import os
        if not os.getenv('DISABLE_AUTO_SETUP'):
            print("🚀 Iniciando configuración automática de la aplicación...")
            self.run_auto_setup()
        else:
            print("⚠️ Configuración automática deshabilitada (DISABLE_AUTO_SETUP=true)")

    def run_auto_setup(self):
        """Ejecuta configuración automática"""
        try:
            print("🔍 Verificando estado de la base de datos...")

            # Ejecutar migraciones
            print("🔄 Paso 1: Ejecutando migraciones automáticamente...")
            from django.core.management import call_command
            call_command('migrate', verbosity=2, interactive=False)
            print("✅ Paso 1 completado: Migraciones ejecutadas exitosamente")

            # Crear superusuario
            print("👤 Paso 2: Verificando superusuario...")
            from django.contrib.auth.models import User

            if not User.objects.filter(username='laika').exists():
                print("📝 Creando superusuario 'laika' con contraseña '11'...")
                User.objects.create_superuser(
                    username='laika',
                    email='laika@example.com',
                    password='11',
                    first_name='Laika',
                    last_name='Admin'
                )
                print("✅ Paso 2 completado: Superusuario 'laika' creado exitosamente")
                print("   Usuario: laika")
                print("   Contraseña: 11")
            else:
                print("✅ Paso 2 completado: Superusuario 'laika' ya existe")

            print("🎉 Configuración automática completada exitosamente!")
            print("🌐 Servidor disponible en: http://localhost:8000")
            print("📚 Documentación API en: http://localhost:8000/docs")

        except Exception as e:
            print(f"❌ Error en configuración automática: {e}")
            import traceback
            traceback.print_exc()
