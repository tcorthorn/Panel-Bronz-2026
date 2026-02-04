"""
Dashboard de Ventas Shopify
Genera estadísticas y datos para visualización
"""

from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncMonth, TruncDate, ExtractHour
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, timedelta


def get_shopify_dashboard_data(fecha_desde=None, fecha_hasta=None):
    """
    Genera todos los datos necesarios para el dashboard de Shopify.
    Permite filtrar por rango de fechas.
    """
    from bronz_app.models import ShopifyOrder
    from django.db.models import Min, Max
    
    # Obtener rango de fechas disponible
    date_range = ShopifyOrder.objects.aggregate(
        min_date=Min('created_at'),
        max_date=Max('created_at')
    )
    
    all_orders = ShopifyOrder.objects.all()
    
    if not all_orders.exists():
        return None
    
    # Aplicar filtro de fechas si se proporcionan
    orders = all_orders
    if fecha_desde:
        orders = orders.filter(created_at__date__gte=fecha_desde)
    if fecha_hasta:
        orders = orders.filter(created_at__date__lte=fecha_hasta)
    
    if not orders.exists():
        return {
            'no_data_in_range': True,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'min_date': date_range['min_date'],
            'max_date': date_range['max_date'],
        }
    
    # ========================================
    # 1. MÉTRICAS PRINCIPALES (KPIs)
    # ========================================
    total_orders = orders.values('order_name').distinct().count()
    total_revenue = orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
    total_items = orders.aggregate(total=Sum('lineitem_quantity'))['total'] or 0
    avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
    
    # Clientes únicos (por email)
    unique_customers = orders.exclude(email='').values('email').distinct().count()
    
    # Tasa de recompra (clientes con más de 1 orden)
    from django.db.models import Count as DjangoCount
    repeat_customers = orders.exclude(email='').values('email').annotate(
        order_count=DjangoCount('order_name', distinct=True)
    ).filter(order_count__gt=1).count()
    repeat_rate = (repeat_customers / unique_customers * 100) if unique_customers > 0 else 0
    
    # ========================================
    # 2. VENTAS POR MES (para gráfico de líneas)
    # ========================================
    sales_by_month = orders.filter(created_at__isnull=False).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True),
        items=Sum('lineitem_quantity')
    ).order_by('month')
    
    months_labels = []
    months_revenue = []
    months_orders = []
    
    for item in sales_by_month:
        if item['month']:
            months_labels.append(item['month'].strftime('%b %Y'))
            months_revenue.append(float(item['total'] or 0))
            months_orders.append(item['orders'] or 0)
    
    # ========================================
    # 3. VENTAS POR DÍA (últimos 30 días)
    # ========================================
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sales_by_day = orders.filter(
        created_at__isnull=False,
        created_at__gte=thirty_days_ago
    ).annotate(
        day=TruncDate('created_at')
    ).values('day').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True)
    ).order_by('day')
    
    days_labels = []
    days_revenue = []
    
    for item in sales_by_day:
        if item['day']:
            days_labels.append(item['day'].strftime('%d/%m'))
            days_revenue.append(float(item['total'] or 0))
    
    # ========================================
    # 4. PRODUCTOS MÁS VENDIDOS (Top 10)
    # ========================================
    # Usar SKU para agrupar y buscar nombre real en Catálogo
    from bronz_app.models import Catalogo
    
    # Crear diccionario de SKU -> nombre del producto desde Catálogo
    catalogo_dict = {}
    for cat in Catalogo.objects.all():
        catalogo_dict[cat.sku.upper()] = cat.producto
    
    # Agrupar por SKU (ignorando el nombre de lineitem que puede tener "PREVENTA")
    top_products_by_sku = orders.exclude(lineitem_sku='').values('lineitem_sku').annotate(
        quantity=Sum('lineitem_quantity'),
        revenue=Sum(F('lineitem_price') * F('lineitem_quantity'))
    ).order_by('-quantity')[:10]
    
    products_labels = []
    products_quantities = []
    products_revenue = []
    
    for product in top_products_by_sku:
        sku = product['lineitem_sku'].upper() if product['lineitem_sku'] else ''
        # Buscar nombre real en catálogo, si no existe usar SKU
        name = catalogo_dict.get(sku, sku)
        if len(name) > 35:
            name = name[:32] + '...'
        products_labels.append(f"{name} ({sku})" if sku else name)
        products_quantities.append(product['quantity'] or 0)
        products_revenue.append(float(product['revenue'] or 0))
    
    # ========================================
    # 5. VENTAS POR CIUDAD (Top 10)
    # ========================================
    # Normalizar ciudades (ignorar mayúsculas/minúsculas)
    from django.db.models.functions import Lower
    
    sales_by_city_raw = orders.exclude(shipping_city='').annotate(
        city_normalized=Lower('shipping_city')
    ).values('city_normalized').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True)
    ).order_by('-total')[:10]
    
    cities_labels = []
    cities_revenue = []
    cities_orders = []
    
    for city in sales_by_city_raw:
        # Capitalizar el nombre de la ciudad para mostrar
        city_name = city['city_normalized'].title() if city['city_normalized'] else ''
        cities_labels.append(city_name)
        cities_revenue.append(float(city['total'] or 0))
        cities_orders.append(city['orders'] or 0)
    
    # ========================================
    # 6. VENTAS POR REGIÓN/PROVINCIA
    # ========================================
    # Normalizar regiones (ignorar mayúsculas/minúsculas)
    sales_by_region = orders.exclude(shipping_province_name='').annotate(
        region_normalized=Lower('shipping_province_name')
    ).values('region_normalized').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True)
    ).order_by('-total')[:10]
    
    # Si no hay datos en shipping_province_name, usar shipping_province
    if not sales_by_region:
        sales_by_region = orders.exclude(shipping_province='').annotate(
            region_normalized=Lower('shipping_province')
        ).values('region_normalized').annotate(
            total=Sum('total'),
            orders=Count('order_name', distinct=True)
        ).order_by('-total')[:10]
    
    regions_labels = [r['region_normalized'].title() if r['region_normalized'] else '' for r in sales_by_region]
    regions_revenue = [float(r['total'] or 0) for r in sales_by_region]
    regions_orders = [r['orders'] or 0 for r in sales_by_region]
    
    # ========================================
    # 7. MÉTODOS DE PAGO
    # ========================================
    payment_methods = orders.exclude(payment_method='').values('payment_method').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True)
    ).order_by('-total')
    
    payment_labels = []
    payment_totals = []
    
    for pm in payment_methods:
        payment_labels.append(pm['payment_method'])
        payment_totals.append(float(pm['total'] or 0))
    
    # ========================================
    # 8. ESTADO DE ÓRDENES
    # ========================================
    # Estado financiero
    financial_status = orders.values('financial_status').annotate(
        count=Count('order_name', distinct=True)
    ).order_by('-count')
    
    fin_status_labels = []
    fin_status_counts = []
    
    status_translation = {
        'paid': 'Pagado',
        'pending': 'Pendiente',
        'refunded': 'Reembolsado',
        'partially_paid': 'Parcialmente Pagado',
        'voided': 'Anulado',
        '': 'Sin estado'
    }
    
    for fs in financial_status:
        status = fs['financial_status'] or ''
        label = status_translation.get(status, status)
        fin_status_labels.append(label)
        fin_status_counts.append(fs['count'] or 0)
    
    # Estado de cumplimiento
    fulfillment_status = orders.values('fulfillment_status').annotate(
        count=Count('order_name', distinct=True)
    ).order_by('-count')
    
    fulf_status_labels = []
    fulf_status_counts = []
    
    fulfillment_translation = {
        'fulfilled': 'Cumplido',
        'unfulfilled': 'No Cumplido',
        'partial': 'Parcial',
        '': 'Sin estado'
    }
    
    for fs in fulfillment_status:
        status = fs['fulfillment_status'] or ''
        label = fulfillment_translation.get(status, status)
        fulf_status_labels.append(label)
        fulf_status_counts.append(fs['count'] or 0)
    
    # ========================================
    # 9. VENTAS POR HORA DEL DÍA
    # ========================================
    sales_by_hour = orders.filter(created_at__isnull=False).annotate(
        hour=ExtractHour('created_at')
    ).values('hour').annotate(
        orders=Count('order_name', distinct=True),
        total=Sum('total')
    ).order_by('hour')
    
    hours_labels = [f"{h}:00" for h in range(24)]
    hours_orders = [0] * 24
    
    for item in sales_by_hour:
        if item['hour'] is not None:
            hours_orders[item['hour']] = item['orders'] or 0
    
    # ========================================
    # 10. TOP CLIENTES
    # ========================================
    top_customers = orders.exclude(email='').values(
        'email', 'billing_name'
    ).annotate(
        total_spent=Sum('total'),
        orders_count=Count('order_name', distinct=True),
        items_count=Sum('lineitem_quantity')
    ).order_by('-total_spent')[:10]
    
    # ========================================
    # 11. ÚLTIMAS ÓRDENES
    # ========================================
    recent_orders = orders.values(
        'order_name', 'customer_name', 'email', 'total', 
        'financial_status', 'fulfillment_status', 'created_at',
        'shipping_city', 'lineitem_name'
    ).order_by('-created_at')[:15]
    
    # ========================================
    # 12. MÉTODOS DE ENVÍO
    # ========================================
    shipping_methods = orders.exclude(shipping_method='').values('shipping_method').annotate(
        orders=Count('order_name', distinct=True),
        total=Sum('total')
    ).order_by('-orders')[:5]
    
    # ========================================
    # 13. DESCUENTOS UTILIZADOS
    # ========================================
    discount_usage = orders.exclude(discount_code='').values('discount_code').annotate(
        times_used=Count('order_name', distinct=True),
        total_discount=Sum('discount_amount'),
        revenue_generated=Sum('total')
    ).order_by('-times_used')[:10]
    
    # ========================================
    # 14. ANÁLISIS DE RENTABILIDAD (NETO DE IVA 19%)
    # ========================================
    IVA = Decimal('1.19')  # Factor IVA Chile
    
    # Crear diccionario de SKU -> costo desde Catálogo
    catalogo_costos = {}
    for cat in Catalogo.objects.all():
        catalogo_costos[cat.sku.upper()] = cat.costo_promedio_neto
    
    # Calcular rentabilidad por producto
    rentabilidad_productos = []
    total_ventas_netas = Decimal('0')
    total_costo = Decimal('0')
    total_utilidad = Decimal('0')
    
    # Agrupar ventas por SKU
    ventas_por_sku = orders.exclude(lineitem_sku='').values('lineitem_sku').annotate(
        cantidad=Sum('lineitem_quantity'),
        venta_bruta=Sum(F('lineitem_price') * F('lineitem_quantity'))
    ).order_by('-venta_bruta')
    
    for item in ventas_por_sku:
        sku = item['lineitem_sku'].upper() if item['lineitem_sku'] else ''
        cantidad = item['cantidad'] or 0
        venta_bruta = Decimal(str(item['venta_bruta'] or 0))
        
        # Calcular venta neta (sin IVA)
        venta_neta = venta_bruta / IVA
        
        # Obtener costo del catálogo
        costo_unitario = catalogo_costos.get(sku, Decimal('0'))
        costo_total = costo_unitario * cantidad
        
        # Calcular utilidad
        utilidad = venta_neta - costo_total
        margen = (utilidad / venta_neta * 100) if venta_neta > 0 else Decimal('0')
        
        # Obtener nombre del producto
        nombre_producto = catalogo_dict.get(sku, sku)
        
        rentabilidad_productos.append({
            'sku': sku,
            'producto': nombre_producto,
            'cantidad': cantidad,
            'venta_bruta': float(venta_bruta),
            'venta_neta': float(venta_neta),
            'costo_unitario': float(costo_unitario),
            'costo_total': float(costo_total),
            'utilidad': float(utilidad),
            'margen': float(margen),
        })
        
        total_ventas_netas += venta_neta
        total_costo += costo_total
        total_utilidad += utilidad
    
    # Ordenar por utilidad (más rentables primero)
    rentabilidad_por_utilidad = sorted(rentabilidad_productos, key=lambda x: x['utilidad'], reverse=True)[:10]
    
    # Ordenar por margen (mejor margen primero)
    rentabilidad_por_margen = sorted(rentabilidad_productos, key=lambda x: x['margen'], reverse=True)[:10]
    
    # KPIs de Rentabilidad
    margen_global = (total_utilidad / total_ventas_netas * 100) if total_ventas_netas > 0 else Decimal('0')
    
    # Datos para gráfico de rentabilidad
    rent_labels = [p['producto'][:20] + '...' if len(p['producto']) > 20 else p['producto'] for p in rentabilidad_por_utilidad]
    rent_utilidades = [p['utilidad'] for p in rentabilidad_por_utilidad]
    rent_margenes = [p['margen'] for p in rentabilidad_por_margen]
    rent_margen_labels = [p['producto'][:20] + '...' if len(p['producto']) > 20 else p['producto'] for p in rentabilidad_por_margen]
    
    # Comparativa Costos vs Ventas por mes
    ventas_costos_mes = []
    for item in sales_by_month:
        if item['month']:
            mes_label = item['month'].strftime('%b %Y')
            venta_bruta_mes = Decimal(str(item['total'] or 0))
            venta_neta_mes = venta_bruta_mes / IVA
            
            # Calcular costo del mes (aproximado basado en productos vendidos ese mes)
            ventas_mes = orders.filter(
                created_at__year=item['month'].year,
                created_at__month=item['month'].month
            ).exclude(lineitem_sku='').values('lineitem_sku').annotate(
                cantidad=Sum('lineitem_quantity')
            )
            
            costo_mes = Decimal('0')
            for v in ventas_mes:
                sku = v['lineitem_sku'].upper() if v['lineitem_sku'] else ''
                costo_unit = catalogo_costos.get(sku, Decimal('0'))
                costo_mes += costo_unit * (v['cantidad'] or 0)
            
            utilidad_mes = venta_neta_mes - costo_mes
            
            ventas_costos_mes.append({
                'mes': mes_label,
                'venta_neta': float(venta_neta_mes),
                'costo': float(costo_mes),
                'utilidad': float(utilidad_mes),
            })
    
    costos_mes_labels = [x['mes'] for x in ventas_costos_mes]
    costos_mes_ventas = [x['venta_neta'] for x in ventas_costos_mes]
    costos_mes_costos = [x['costo'] for x in ventas_costos_mes]
    costos_mes_utilidades = [x['utilidad'] for x in ventas_costos_mes]
    
    # ========================================
    # COMPILAR DATOS
    # ========================================
    return {
        # KPIs principales
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'avg_order_value': avg_order_value,
        'unique_customers': unique_customers,
        'repeat_rate': round(repeat_rate, 1),
        
        # Gráficos de ventas
        'months_labels': months_labels,
        'months_revenue': months_revenue,
        'months_orders': months_orders,
        
        'days_labels': days_labels,
        'days_revenue': days_revenue,
        
        # Productos
        'products_labels': products_labels,
        'products_quantities': products_quantities,
        'products_revenue': products_revenue,
        
        # Geografía
        'cities_labels': cities_labels,
        'cities_revenue': cities_revenue,
        'cities_orders': cities_orders,
        
        'regions_labels': regions_labels,
        'regions_revenue': regions_revenue,
        'regions_orders': regions_orders,
        
        # Pagos
        'payment_labels': payment_labels,
        'payment_totals': payment_totals,
        
        # Estados
        'fin_status_labels': fin_status_labels,
        'fin_status_counts': fin_status_counts,
        'fulf_status_labels': fulf_status_labels,
        'fulf_status_counts': fulf_status_counts,
        
        # Horarios
        'hours_labels': hours_labels,
        'hours_orders': hours_orders,
        
        # Tablas
        'top_customers': list(top_customers),
        'recent_orders': list(recent_orders),
        'shipping_methods': list(shipping_methods),
        'discount_usage': list(discount_usage),
        
        # Fechas para el filtro
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'min_date': date_range['min_date'],
        'max_date': date_range['max_date'],
        
        # ========== RENTABILIDAD (NETO IVA 19%) ==========
        'total_ventas_netas': float(total_ventas_netas),
        'total_costo': float(total_costo),
        'total_utilidad': float(total_utilidad),
        'margen_global': float(margen_global),
        
        # Tablas de rentabilidad
        'rentabilidad_por_utilidad': rentabilidad_por_utilidad,
        'rentabilidad_por_margen': rentabilidad_por_margen,
        
        # Gráficos de rentabilidad
        'rent_labels': rent_labels,
        'rent_utilidades': rent_utilidades,
        'rent_margen_labels': rent_margen_labels,
        'rent_margenes': rent_margenes,
        
        # Comparativa mensual Costos vs Ventas
        'costos_mes_labels': costos_mes_labels,
        'costos_mes_ventas': costos_mes_ventas,
        'costos_mes_costos': costos_mes_costos,
        'costos_mes_utilidades': costos_mes_utilidades,
    }
