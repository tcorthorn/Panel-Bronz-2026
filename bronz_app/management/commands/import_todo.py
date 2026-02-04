#IMPORTA DATOS DE TABLA ACCESS A SQLITE

from django.core.management.base import BaseCommand
import subprocess, os

class Command(BaseCommand):
    help = "Importa todas las tablas a la vez"

    def handle(self, *args, **options):
        scripts = [
           "import_catalogo.py",
            "import_ventas.py",
            "import_envios.py",
            "import_otros_gastos.py",
            "import_asientos_contables.py",
            "import_balance_inicial.py",
            "import_entrada_productos.py",
            "import_inventario_inicial.py",
            

        ]
        for script in scripts:
            self.stdout.write(self.style.NOTICE(f"Ejecutando {script}..."))
            result = subprocess.run(["python", script], capture_output=True, text=True)
            self.stdout.write(result.stdout)
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"Error ejecutando {script}:"))
                self.stdout.write(result.stderr)
                break
        self.stdout.write(self.style.SUCCESS("Importaciones completas."))

        os.system('python manage.py migrate --fake-initial')