"""
Dashboard de Ventas Shopify
Genera estadísticas y datos para visualización
"""

from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncMonth, TruncDate, ExtractHour
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, timedelta


def get_shopify_dashboard_data():
    """
    Genera todos los datos necesarios para el dashboard de Shopify.
    """
    from bronz_app.models import ShopifyOrder
    
    orders = ShopifyOrder.objects.all()
    
    if not orders.exists():
        return None
    
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
    top_products = orders.exclude(lineitem_name='').values('lineitem_name', 'lineitem_sku').annotate(
        quantity=Sum('lineitem_quantity'),
        revenue=Sum(F('lineitem_price') * F('lineitem_quantity'))
    ).order_by('-quantity')[:10]
    
    products_labels = []
    products_quantities = []
    products_revenue = []
    
    for product in top_products:
        name = product['lineitem_name'][:30] + '...' if len(product['lineitem_name']) > 30 else product['lineitem_name']
        products_labels.append(name)
        products_quantities.append(product['quantity'] or 0)
        products_revenue.append(float(product['revenue'] or 0))
    
    # ========================================
    # 5. VENTAS POR CIUDAD (Top 10)
    # ========================================
    sales_by_city = orders.exclude(shipping_city='').values('shipping_city').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True)
    ).order_by('-total')[:10]
    
    cities_labels = []
    cities_revenue = []
    cities_orders = []
    
    for city in sales_by_city:
        cities_labels.append(city['shipping_city'])
        cities_revenue.append(float(city['total'] or 0))
        cities_orders.append(city['orders'] or 0)
    
    # ========================================
    # 6. VENTAS POR REGIÓN/PROVINCIA
    # ========================================
    sales_by_region = orders.exclude(shipping_province_name='').values('shipping_province_name').annotate(
        total=Sum('total'),
        orders=Count('order_name', distinct=True)
    ).order_by('-total')[:10]
    
    # Si no hay datos en shipping_province_name, usar shipping_province
    if not sales_by_region:
        sales_by_region = orders.exclude(shipping_province='').values('shipping_province').annotate(
            total=Sum('total'),
            orders=Count('order_name', distinct=True)
        ).order_by('-total')[:10]
        
        regions_labels = [r['shipping_province'] for r in sales_by_region]
    else:
        regions_labels = [r['shipping_province_name'] for r in sales_by_region]
    
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
    }
