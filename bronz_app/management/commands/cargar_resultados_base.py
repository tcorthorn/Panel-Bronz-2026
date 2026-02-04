from django.core.management.base import BaseCommand
from datetime import date
from bronz_app.models import ResultadoMensualDetalle

class Command(BaseCommand):
    help = "Carga conceptos base de resultados para todos los meses del año actual"

    def handle(self, *args, **kwargs):
        conceptos = [
            "ventas",
            "costo_venta",
            "gastos_comercializacion",
            "gastos_marketing",
            "gastos_arriendos",
            "gastos_envios",
            "gastos_administracion",
            "gastos_financieros",
            "depreciacion",
            "utilidad_no_operacional",
            "ajuste_monetario",
            "impuesto_renta",
            "ajustes",
            # Agrega más si tus bases lo requieren
        ]
        año = date.today().year
        count = 0
        for mes in range(1, 13):
            mes_date = date(año, mes, 1)
            for concepto in conceptos:
                obj, creado = ResultadoMensualDetalle.objects.get_or_create(
                    mes=mes_date,
                    concepto=concepto,
                    defaults={"valor": 0}
                )
                if creado:
                    count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Se cargaron {count} conceptos base para cada mes de {año}."
        ))
