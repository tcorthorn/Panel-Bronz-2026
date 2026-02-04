from django.core.management.base import BaseCommand
from bronz_app.utils import (
    regenerar_tabla_ventas_consulta,
    poblar_movimientos_unificados_credito,
    poblar_movimientos_unificados_debito,
    regenerar_resumenes_credito_debito,
)
import sys
import traceback

def safe_print(msg):
    print(msg.encode("ascii", "replace").decode("ascii"))

class Command(BaseCommand):
    help = "Regenera todas las tablas: VentasConsulta, Movimientos Unificados (crédito/débito) y resúmenes."

    def handle(self, *args, **options):
        try:
            safe_print("[1/4] Regenerando tabla VentasConsulta...")
            regenerar_tabla_ventas_consulta()
            safe_print("[OK] VentasConsulta regenerada.")

            safe_print("[2/4] Poblando movimientos unificados crédito...")
            count_credito = poblar_movimientos_unificados_credito()
            safe_print(f"[OK] Se poblaron {count_credito} movimientos crédito.")

            safe_print("[3/4] Poblando movimientos unificados débito...")
            count_debito = poblar_movimientos_unificados_debito()
            safe_print(f"[OK] Se poblaron {count_debito} movimientos débito.")

            safe_print("[4/4] Regenerando resúmenes crédito y débito...")
            c, d = regenerar_resumenes_credito_debito()
            safe_print(f"[OK] Resumen crédito ({c}), Resumen débito ({d}) generado.")

            safe_print("\n[FINALIZADO] Todas las tablas se han generado correctamente.")

        except Exception as e:
            safe_print("\n[ERROR] Ocurrió un error:")
            safe_print(str(e))
            traceback.print_exc()
            sys.exit(1)