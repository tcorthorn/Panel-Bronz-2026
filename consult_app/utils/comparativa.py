# consult_app/utils/comparativa.py
from consult_app.models import ProyeccionVenta 
from bronz_app.models import ResumenMensual
from decimal import Decimal

def generar_comparativa(anio: int):
    """
    Genera una lista comparando las ventas reales (ResumenMensual)
    con las proyecciones (ProyeccionVenta), incluyendo IVA (1.19).
    """
    comparativa = []
    IVA_FACTOR = Decimal('1.19')  # 👈 IVA definido como Decimal

    for mes in range(1, 13):
        # Buscar la proyección
        proy = ProyeccionVenta.objects.filter(anio=anio, mes=mes).first()
        proy_valor = proy.venta_proyectada if proy else Decimal(0)

        # Buscar el resumen mensual real
        resumen = ResumenMensual.objects.filter(mes__year=anio, mes__month=mes).first()
        real_valor = resumen.ventas if resumen else Decimal(0)

        # 🔹 Aplicar IVA sobre las ventas reales (ambos Decimals)
        real_con_iva = real_valor * IVA_FACTOR

        # Calcular diferencias y % cumplimiento
        diferencia = real_con_iva - proy_valor
        cumplimiento = (real_con_iva / proy_valor * 100) if proy_valor > 0 else 0

        comparativa.append({
            'anio': anio,
            'mes': mes,
            'venta_proyectada': float(proy_valor),
            'venta_real': float(real_con_iva),
            'diferencia': float(diferencia),
            'cumplimiento': round(cumplimiento, 2),
        })

    return comparativa

