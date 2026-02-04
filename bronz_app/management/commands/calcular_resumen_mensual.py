# management/commands/calcular_resumen_mensual.py

from django.core.management.base import BaseCommand
from bronz_app.models import MovimientoUnificadoDebito, MovimientoUnificadoCredito, ResumenMensual
from django.db.models import Sum
from collections import defaultdict
from django.db.models.functions import TruncMonth

CUENTAS_VENTAS = [3010101, 3010111]
CUENTA_COSTO = 3010200

class Command(BaseCommand):
    help = 'Calcula y guarda el resumen financiero mensual'

    def handle(self, *args, **kwargs):
        saldos_mensuales = defaultdict(lambda: defaultdict(lambda: {'debitos': 0, 'creditos': 0}))

        # Débitos agrupados por mes
        for row in (MovimientoUnificadoDebito.objects.annotate(mes=TruncMonth('fecha'))
                    .values('cta_debito', 'mes')
                    .annotate(total=Sum('monto_debito'))):
            cuenta = int(row['cta_debito'])
            mes = row['mes']
            saldos_mensuales[mes][cuenta]['debitos'] += row['total'] or 0

        # Créditos agrupados por mes
        for row in (MovimientoUnificadoCredito.objects.annotate(mes=TruncMonth('fecha'))
                    .values('cta_credito', 'mes')
                    .annotate(total=Sum('monto_credito'))):
            cuenta = int(row['cta_credito'])
            mes = row['mes']
            saldos_mensuales[mes][cuenta]['creditos'] += row['total'] or 0

        for mes, cuentas in saldos_mensuales.items():
            ventas = sum(
                cuentas[cuenta]['debitos'] - cuentas[cuenta]['creditos']
                for cuenta in CUENTAS_VENTAS if cuenta in cuentas
            )
            costos = cuentas.get(CUENTA_COSTO, {'debitos': 0, 'creditos': 0})
            costo_venta = costos['debitos'] - costos['creditos']
            utilidad = ventas - costo_venta
            margen_bruto = utilidad

            ResumenMensual.objects.update_or_create(
                mes=mes,
                defaults={
                    'ventas': ventas,
                    'costos': costo_venta,
                    'utilidad': utilidad,
                    'margen_bruto': margen_bruto
                }
            )

        self.stdout.write(self.style.SUCCESS('Resumen mensual actualizado.'))
