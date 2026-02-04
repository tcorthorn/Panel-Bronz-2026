from django.db import transaction
from django.db.models import F, Value, TextField, DecimalField, Sum
from django.db.models.functions import Cast, Coalesce
from datetime import date
from bronz_app.models import (
    OtrosGastos,
    SueldosHonorarios,
    AsientosContables,
    EntradaProductos,
    BalanceInicial,
    Ventas,
    VentasConsulta,
    MovimientoUnificadoCredito,
    MovimientoUnificadoDebito,
    ResumenCredito,
    ResumenDebito,
)

# ——————————————————————————————————————————————————————————————
#   VENTAS CONSULTA
# ————————————————————————————————————————————————————————

def regenerar_ventas_consulta(start_date=None, end_date=None):
    """
    Regenera la tabla VentasConsulta.
    Si se proporcionan fechas, solo borra y regenera ventas dentro del rango.
    """
    if start_date and end_date:
        VentasConsulta.objects.filter(
            fecha__gte=start_date,
            fecha__lte=end_date
        ).delete()
    else:
        VentasConsulta.objects.all().delete()

    ventas = Ventas.objects.select_related('sku').all()
    
    if start_date:
        ventas = ventas.filter(fecha__gte=start_date)
    if end_date:
        ventas = ventas.filter(fecha__lte=end_date)

    consultas = []
    for venta in ventas:
        sku_data = venta.sku
        costo_venta = sku_data.costo_promedio_neto * venta.cantidad

        consultas.append(VentasConsulta(
            fecha=venta.fecha,
            codigo_producto=sku_data.sku,
            comprador=venta.comprador,
            cantidad=venta.cantidad,
            total_venta=venta.total_venta,
            cuenta_debito=venta.cuenta_debito,
            debito=venta.debito,
            cuenta_credito=venta.cuenta_credito,
            cuenta_debito_eerr=venta.cuenta_debito_eerr,
            debito_eerr=venta.debito_eerr,
            cuenta_credito_eerr=venta.cuenta_credito_eerr,
            credito_eerr=venta.credito_eerr,
            costo_promedio_neto=sku_data.costo_promedio_neto,
            comentario=venta.comentario,
            costo_venta=costo_venta,
            categoria=sku_data.categoria,
            producto=sku_data.producto,
            cuenta_debito_envio=venta.cuenta_debito_envio,
            credito_iva=venta.credito_iva,
            venta_neta_iva=venta.venta_neta_de_iva,
            credito_envio=venta.credito_envio,
            debito_envio=venta.debito_envio
        ))

    VentasConsulta.objects.bulk_create(consultas)
    return len(consultas)


# ——————————————————————————————————————————————————————————————
# FUNCIONES AUXILIARES PARA QUERIES
# ——————————————————————————————————————————————————————————————

def make_query(modelo, cta_field, monto_field, coment_field, tabla_origen, start_date=None, end_date=None):
    """
    Genera un queryset anotado para débitos con filtros de fecha opcionales.
    """
    qs = modelo.objects.all()
    
    if start_date:
        qs = qs.filter(fecha__gte=start_date)
    if end_date:
        qs = qs.filter(fecha__lte=end_date)
    
    anotaciones = {
        'cta_debito': Cast(F(cta_field), output_field=TextField()),
        'monto_debito': Cast(F(monto_field), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'tabla_origen': Value(tabla_origen, output_field=TextField()),
    }

    if coment_field:
        anotaciones['texto_coment'] = Coalesce(
            Cast(F(coment_field), output_field=TextField()),
            Value('', output_field=TextField())
        )
    else:
        anotaciones['texto_coment'] = Value('', output_field=TextField())

    return qs.annotate(**anotaciones).values(
        'fecha', 'cta_debito', 'monto_debito', 'texto_coment', 'tabla_origen'
    )


def make_query_credito(queryset, cta_field, monto_field, coment_field, tabla_origen, usar_cast=False, start_date=None, end_date=None):
    """
    Genera un queryset anotado para créditos con filtros de fecha opcionales.
    """
    if hasattr(queryset, 'all'):
        qs = queryset.all()
    else:
        qs = queryset
    
    if start_date:
        qs = qs.filter(fecha__gte=start_date)
    if end_date:
        qs = qs.filter(fecha__lte=end_date)
    
    anotaciones = {
        'cta_credito': Cast(F(cta_field), output_field=TextField()),
        'monto_credito': Cast(F(monto_field), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'tabla_origen': Value(tabla_origen, output_field=TextField()),
    }
    
    if coment_field:
        anotaciones['texto_coment'] = Coalesce(
            Cast(F(coment_field), output_field=TextField()),
            Value('', output_field=TextField())
        )
    else:
        anotaciones['texto_coment'] = Value('', output_field=TextField())

    return qs.annotate(**anotaciones).values(
        'fecha', 'cta_credito', 'monto_credito', 'texto_coment', 'tabla_origen'
    )


# ——————————————————————————————————————————————————————————————
# CONSULTA DEBITOS
# ——————————————————————————————————————————————————————————————

def poblar_movimientos_unificados_debito(start_date=None, end_date=None):
    qs_otros = make_query(OtrosGastos, 'cuenta_debito', 'debito', 'comentario', 'Otros Gastos', start_date, end_date)
    qs_otros_eerr = make_query(OtrosGastos, 'cuenta_debito_eerr', 'debito_eerr', 'comentario', 'Otros Gastos (EERR)', start_date, end_date)
    qs_sueldos = make_query(SueldosHonorarios, 'cuenta_debito', 'debito', 'comentario', 'Sueldos y Honorarios', start_date, end_date)
    qs_asientos = make_query(AsientosContables, 'cuenta_debito', 'debito', 'comentario', 'Asientos Contables', start_date, end_date)
    qs_entradas_debito = make_query(EntradaProductos, 'cuenta_debito', 'debito', 'comentario', 'Entrada de Productos', start_date, end_date)
    qs_entradas_iva = make_query(EntradaProductos, 'cuenta_debito_iva', 'debito_iva', 'comentario', 'Entrada de Productos (IVA)', start_date, end_date)
    qs_balance_inicial = make_query(BalanceInicial, 'cuenta_debito', 'debito', 'comentario', 'Balance Inicial', start_date, end_date)
    qs_ventas = make_query(Ventas, 'cuenta_debito', 'debito', 'comentario', 'Ventas', start_date, end_date)
    qs_ventas_envio = make_query(Ventas, 'cuenta_debito_envio', 'debito_envio', 'comentario', 'Ventas (EERR)', start_date, end_date)
    qs_ventas_iva_plataformas = make_query(Ventas, 'cuenta_debito_iva_plataformas', 'debito_iva_plataformas', 'comentario', 'Ventas (Plataformas)', start_date, end_date)
    qs_ventas_plataformas = make_query(Ventas, 'cuenta_debito_plataformas', 'debito_plataformas', 'comentario', 'Ventas (Plataformas)', start_date, end_date)
    qs_ventas_consulta = make_query(VentasConsulta, 'cuenta_debito_eerr', 'costo_venta', 'comentario', 'Ventas Consulta', start_date, end_date)

    union_qs = qs_otros.union(
        qs_otros_eerr, qs_sueldos, qs_asientos, qs_entradas_debito, qs_entradas_iva, qs_balance_inicial,
        qs_ventas, qs_ventas_envio, qs_ventas_iva_plataformas, qs_ventas_plataformas, qs_ventas_consulta, all=True
    )

    with transaction.atomic():
        if start_date and end_date:
            MovimientoUnificadoDebito.objects.filter(
                fecha__gte=start_date,
                fecha__lte=end_date
            ).delete()
        else:
            MovimientoUnificadoDebito.objects.all().delete()
            
        objetos = [
            MovimientoUnificadoDebito(
                fecha=row['fecha'],
                cta_debito=row['cta_debito'],
                monto_debito=row['monto_debito'],
                texto_coment=row['texto_coment'] or '',
                tabla_origen=row['tabla_origen']
            )
            for row in union_qs
        ]
        MovimientoUnificadoDebito.objects.bulk_create(objetos)
        return len(objetos)


# ——————————————————————————————————————————————————————————————
# CONSULTA CREDITOS
# ——————————————————————————————————————————————————————————————

def poblar_movimientos_unificados_credito(start_date=None, end_date=None):
    qs_otros = make_query_credito(OtrosGastos.objects, 'cuenta_credito', 'credito', 'comentario', 'Otros Gastos', start_date=start_date, end_date=end_date)
    qs_sueldos = make_query_credito(SueldosHonorarios.objects, 'cuenta_credito', 'credito', 'comentario', 'Sueldos y Honorarios', start_date=start_date, end_date=end_date)
    qs_sueldos_2 = make_query_credito(SueldosHonorarios.objects, 'cuenta_credito2', 'credito2', 'comentario', 'Sueldos y Honorarios (2)', start_date=start_date, end_date=end_date)
    qs_asientos = make_query_credito(AsientosContables.objects, 'cuenta_credito', 'credito', 'comentario', 'Asientos Contables', start_date=start_date, end_date=end_date)
    qs_entradas = make_query_credito(EntradaProductos.objects, 'cuenta_credito', 'credito', 'comentario', 'Entrada de Productos', usar_cast=True, start_date=start_date, end_date=end_date)
    qs_balance_inicial = make_query_credito(BalanceInicial.objects, 'cuenta_credito', 'credito', 'comentario', 'Balance Inicial', start_date=start_date, end_date=end_date)
    qs_ventas_consulta = make_query_credito(VentasConsulta.objects, 'cuenta_credito', 'costo_venta', 'comentario', 'Ventas Consulta', start_date=start_date, end_date=end_date)
    qs_ventas_eerr = make_query_credito(Ventas.objects.exclude(credito_eerr=0).exclude(credito_eerr__isnull=True), 'cuenta_credito_eerr', 'venta_neta_de_iva', 'comentario', 'Ventas (EERR)', start_date=start_date, end_date=end_date)
    qs_ventas_iva = make_query_credito(Ventas.objects.exclude(credito_iva=0).exclude(credito_iva__isnull=True), 'cuenta_credito_iva', 'credito_iva', 'comentario', 'Ventas (IVA)', start_date=start_date, end_date=end_date)
    qs_ventas_envio = make_query_credito(Ventas.objects, 'cuenta_credito_envio', 'credito_envio', 'comentario', 'Ventas (ENVIO)', start_date=start_date, end_date=end_date)
    qs_ventas_plataformas = make_query_credito(Ventas.objects, 'cuenta_credito_plataformas', 'credito_plataformas', 'comentario', 'Ventas (Plataformas)', start_date=start_date, end_date=end_date)

    union_qs = qs_otros.union(qs_sueldos, qs_asientos, qs_entradas, qs_sueldos_2, qs_balance_inicial,
               qs_ventas_consulta, qs_ventas_eerr, qs_ventas_iva, qs_ventas_envio, qs_ventas_plataformas, all=True)

    with transaction.atomic():
        if start_date and end_date:
            MovimientoUnificadoCredito.objects.filter(
                fecha__gte=start_date,
                fecha__lte=end_date
            ).delete()
        else:
            MovimientoUnificadoCredito.objects.all().delete()
            
        objetos = [
            MovimientoUnificadoCredito(
                fecha=row['fecha'],
                cta_credito=row['cta_credito'],
                monto_credito=row['monto_credito'],
                texto_coment=row['texto_coment'],
                tabla_origen=row['tabla_origen']
            )
            for row in union_qs
        ]
        MovimientoUnificadoCredito.objects.bulk_create(objetos)
        return len(objetos)


# ——————————————————————————————————————————————————————————————
# SUMA CREDITOS y DEBITOS
# ——————————————————————————————————————————————————————————————

def regenerar_resumenes_credito_debito():
    ResumenCredito.objects.all().delete()
    ResumenDebito.objects.all().delete()

    creditos_agrupados = (
        MovimientoUnificadoCredito.objects
        .values('cta_credito')
        .annotate(total_credito=Sum('monto_credito'))
    )

    debitos_agrupados = (
        MovimientoUnificadoDebito.objects
        .values('cta_debito')
        .annotate(total_debito=Sum('monto_debito'))
    )

    resumen_credito_objs = [
        ResumenCredito(cuenta_credito=c['cta_credito'], total_credito=c['total_credito'])
        for c in creditos_agrupados
    ]

    resumen_debito_objs = [
        ResumenDebito(cuenta_debito=d['cta_debito'], total_debito=d['total_debito'])
        for d in debitos_agrupados
    ]

    ResumenCredito.objects.bulk_create(resumen_credito_objs)
    ResumenDebito.objects.bulk_create(resumen_debito_objs)

    return len(resumen_credito_objs), len(resumen_debito_objs)
