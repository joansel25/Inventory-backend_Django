from django.core.management.base import BaseCommand
from apps.usuario.models import Usuario

class Command(BaseCommand):
    help = 'Establece la contraseña de un usuario manualmente (hasheada).'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('password', type=str, help='Nueva contraseña')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        try:
            user = Usuario.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Contraseña actualizada correctamente para el usuario '{username}'."))
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"El usuario '{username}' no existe."))
