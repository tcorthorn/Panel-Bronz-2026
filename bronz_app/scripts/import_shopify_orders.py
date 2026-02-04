"""
Script DEFINITIVO para importar órdenes de Shopify desde archivo CSV.
Compatible con el formato de exportación estándar de Shopify.

SOLUCIÓN COMPLETA:
- Maneja CSVs con formato especial de Shopify (filas envueltas en comillas)
- Todos los campos TextField para evitar límites de longitud
- Detección automática de duplicados (modo APPEND)
- Manejo robusto de errores por fila
- Reportes detallados de importación

Autor: Generado para Panel-Bronz
Fecha: 2025
"""

def main():
    import sys
    import os
    import csv
    import re
    from decimal import Decimal, InvalidOperation
    from datetime import datetime
    
    # Configuración Django
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    sys.path.insert(0, PROJECT_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BRONZ.settings")
    
    import django
    django.setup()
    
    from bronz_app.models import ShopifyOrder
    
    # =========================================================================
    # BÚSQUEDA DEL ARCHIVO CSV
    # =========================================================================
    possible_paths = [
        os.path.join(PROJECT_DIR, "data", "orders_export.csv"),
        os.path.join(PROJECT_DIR, "data", "orders_export (1).csv"),
        os.path.join(PROJECT_DIR, "Otros", "orders_export.csv"),
        os.path.join(PROJECT_DIR, "Otros", "orders_export (1).csv"),
        # Windows paths
        r"C:\Users\Thomas\OneDrive\BRONZ\Django-Bronz\data\orders_export.csv",
        r"C:\Users\Thomas\OneDrive\BRONZ\Django-Bronz\Otros\orders_export.csv",
        r"C:\Panel-Bronz-2026-main\data\orders_export.csv",
        r"C:\Panel-Bronz-2026-main\Otros\orders_export.csv",
    ]
    
    archivo_csv = None
    for path in possible_paths:
        if os.path.exists(path):
            archivo_csv = path
            break
    
    if archivo_csv is None:
        return "❌ No se encontró el archivo CSV de órdenes Shopify. Coloque el archivo en la carpeta 'data' o 'Otros' con nombre 'orders_export.csv'"
    
    # =========================================================================
    # FUNCIONES AUXILIARES DE CONVERSIÓN SEGURA
    # =========================================================================
    
    def safe_str(val, max_length=None):
        """Convierte a string de forma segura, opcionalmente truncando."""
        if val is None:
            return ""
        val_str = str(val).strip()
        if val_str.lower() in ('nan', 'none', 'null'):
            return ""
        # Limpiar comillas dobles escapadas
        val_str = val_str.replace('""', '"').strip('"')
        if max_length and len(val_str) > max_length:
            return val_str[:max_length]
        return val_str
    
    def safe_decimal(val, default='0.00'):
        """Convierte a Decimal de forma segura."""
        try:
            if val is None:
                return Decimal(default)
            val_str = str(val).strip().replace(',', '').replace('""', '').strip('"')
            if val_str == "" or val_str.lower() in ('nan', 'none', 'null'):
                return Decimal(default)
            return Decimal(val_str)
        except (InvalidOperation, ValueError):
            return Decimal(default)
    
    def safe_int(val, default=0):
        """Convierte a entero de forma segura."""
        try:
            if val is None:
                return default
            val_str = str(val).strip().replace(',', '').replace('""', '').strip('"')
            if val_str == "" or val_str.lower() in ('nan', 'none', 'null'):
                return default
            return int(float(val_str))
        except (ValueError, TypeError):
            return default
    
    def safe_bool(val, default=False):
        """Convierte a booleano de forma segura."""
        if val is None:
            return default
        val_str = str(val).strip().lower().replace('""', '').strip('"')
        if val_str in ('true', 'yes', 'si', 'sí', '1'):
            return True
        elif val_str in ('false', 'no', '0', ''):
            return False
        return default
    
    def parse_datetime(val):
        """Parsea una fecha/hora de Shopify con múltiples formatos."""
        if val is None:
            return None
        
        val_str = str(val).strip().replace('""', '').strip('"')
        if val_str == "" or val_str.lower() in ('nan', 'none', 'null'):
            return None
        
        # Formatos comunes de Shopify
        formats = [
            "%Y-%m-%d %H:%M:%S %z",      # 2026-01-19 20:36:01 -0300
            "%Y-%m-%d %H:%M:%S",          # 2026-01-19 20:36:01
            "%Y-%m-%dT%H:%M:%S%z",        # ISO format con timezone
            "%Y-%m-%dT%H:%M:%S",          # ISO sin timezone
            "%d/%m/%Y %H:%M:%S",          # Formato DD/MM/YYYY
            "%d/%m/%Y",                    # Solo fecha
            "%Y-%m-%d",                    # Solo fecha ISO
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue
        
        return None

    # =========================================================================
    # MAPEO DE COLUMNAS CSV A CAMPOS DEL MODELO
    # =========================================================================
    COLUMN_MAP = {
        'Name': 'order_name',
        'Email': 'email',
        'Financial Status': 'financial_status',
        'Paid at': 'paid_at',
        'Fulfillment Status': 'fulfillment_status',
        'Fulfilled at': 'fulfilled_at',
        'Accepts Marketing': 'accepts_marketing',
        'Currency': 'currency',
        'Subtotal': 'subtotal',
        'Shipping': 'shipping_amount',
        'Taxes': 'taxes',
        'Total': 'total',
        'Discount Code': 'discount_code',
        'Discount Amount': 'discount_amount',
        'Shipping Method': 'shipping_method',
        'Created at': 'created_at',
        'Lineitem quantity': 'lineitem_quantity',
        'Lineitem name': 'lineitem_name',
        'Lineitem price': 'lineitem_price',
        'Lineitem compare at price': 'lineitem_compare_at_price',
        'Lineitem sku': 'lineitem_sku',
        'Lineitem requires shipping': 'lineitem_requires_shipping',
        'Lineitem taxable': 'lineitem_taxable',
        'Lineitem fulfillment status': 'lineitem_fulfillment_status',
        'Billing Name': 'billing_name',
        'Billing Street': 'billing_street',
        'Billing Address1': 'billing_address1',
        'Billing Address2': 'billing_address2',
        'Billing Company': 'billing_company',
        'Billing City': 'billing_city',
        'Billing Zip': 'billing_zip',
        'Billing Province': 'billing_province',
        'Billing Country': 'billing_country',
        'Billing Phone': 'billing_phone',
        'Shipping Name': 'shipping_name',
        'Shipping Street': 'shipping_street',
        'Shipping Address1': 'shipping_address1',
        'Shipping Address2': 'shipping_address2',
        'Shipping Company': 'shipping_company',
        'Shipping City': 'shipping_city',
        'Shipping Zip': 'shipping_zip',
        'Shipping Province': 'shipping_province',
        'Shipping Country': 'shipping_country',
        'Shipping Phone': 'shipping_phone',
        'Notes': 'notes',
        'Note Attributes': 'note_attributes',
        'Cancelled at': 'cancelled_at',
        'Payment Method': 'payment_method',
        'Payment Reference': 'payment_reference',
        'Refunded Amount': 'refunded_amount',
        'Vendor': 'vendor',
        'Outstanding Balance': 'outstanding_balance',
        'Employee': 'employee',
        'Location': 'location',
        'Device ID': 'device_id',
        'Id': 'shopify_id',
        'Tags': 'tags',
        'Risk Level': 'risk_level',
        'Source': 'source',
        'Lineitem discount': 'lineitem_discount',
        'Tax 1 Name': 'tax_1_name',
        'Tax 1 Value': 'tax_1_value',
        'Tax 2 Name': 'tax_2_name',
        'Tax 2 Value': 'tax_2_value',
        'Tax 3 Name': 'tax_3_name',
        'Tax 3 Value': 'tax_3_value',
        'Tax 4 Name': 'tax_4_name',
        'Tax 4 Value': 'tax_4_value',
        'Tax 5 Name': 'tax_5_name',
        'Tax 5 Value': 'tax_5_value',
        'Phone': 'phone',
        'Receipt Number': 'receipt_number',
        'Duties': 'duties',
        'Billing Province Name': 'billing_province_name',
        'Shipping Province Name': 'shipping_province_name',
        'Payment ID': 'payment_id',
        'Payment Terms Name': 'payment_terms_name',
        'Next Payment Due At': 'next_payment_due_at',
        'Payment References': 'payment_references',
    }
    
    # Tipos de campos
    DATE_FIELDS = ['paid_at', 'fulfilled_at', 'created_at', 'cancelled_at', 'next_payment_due_at']
    DECIMAL_FIELDS = [
        'subtotal', 'shipping_amount', 'taxes', 'total', 'discount_amount',
        'lineitem_price', 'lineitem_compare_at_price', 'lineitem_discount',
        'refunded_amount', 'outstanding_balance', 'duties',
        'tax_1_value', 'tax_2_value', 'tax_3_value', 'tax_4_value', 'tax_5_value'
    ]
    INT_FIELDS = ['lineitem_quantity', 'shopify_id']
    BOOL_FIELDS = ['accepts_marketing', 'lineitem_requires_shipping', 'lineitem_taxable']

    # =========================================================================
    # FUNCIÓN PARA PARSEAR CSV CON FORMATO ESPECIAL DE SHOPIFY
    # =========================================================================
    
    def parse_shopify_csv(filepath):
        """
        Parser especial para CSVs de Shopify que pueden tener filas
        envueltas en comillas dobles con escape interno.
        """
        rows = []
        headers = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detectar si la línea está envuelta en comillas (formato especial)
            if line.startswith('"') and line.endswith('"') and line.count('","') == 0:
                # Quitar las comillas externas y procesar
                line = line[1:-1]
                # Las comillas dobles internas son escapes
                line = line.replace('""', '\x00')  # Placeholder temporal
            
            # Parsear usando csv
            try:
                reader = csv.reader([line])
                parsed_row = next(reader)
                # Restaurar comillas escapadas
                parsed_row = [cell.replace('\x00', '"') for cell in parsed_row]
                
                if line_num == 0:
                    # Es el header - limpiar nombres de columnas
                    headers = [h.strip().rstrip(';') for h in parsed_row]
                else:
                    if len(parsed_row) >= len(headers) * 0.5:  # Al menos 50% de campos
                        rows.append(dict(zip(headers, parsed_row)))
            except Exception as e:
                continue  # Ignorar líneas mal formateadas
        
        return headers, rows

    # =========================================================================
    # OBTENER REGISTROS EXISTENTES PARA EVITAR DUPLICADOS
    # =========================================================================
    
    existing_keys = set()
    existing_records = ShopifyOrder.objects.values_list('order_name', 'lineitem_sku', 'lineitem_name')
    for order_name, sku, lineitem in existing_records:
        key = f"{order_name or ''}|{sku or ''}|{lineitem or ''}"
        existing_keys.add(key)
    
    total_existentes_antes = ShopifyOrder.objects.count()
    
    # =========================================================================
    # PROCESAR EL ARCHIVO CSV
    # =========================================================================
    
    ordenes_creadas = 0
    ordenes_duplicadas = 0
    errores = []
    filas_procesadas = 0
    
    try:
        # Intentar primero con el parser especial
        headers, rows = parse_shopify_csv(archivo_csv)
        
        if not rows:
            # Fallback a csv.DictReader estándar
            with open(archivo_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                headers = reader.fieldnames
        
        for row_num, row in enumerate(rows, start=2):
            filas_procesadas += 1
            
            try:
                # Construir el diccionario de datos
                data = {}
                
                for csv_col, model_field in COLUMN_MAP.items():
                    raw_value = row.get(csv_col, "")
                    
                    # Convertir según el tipo de campo
                    if model_field in DATE_FIELDS:
                        data[model_field] = parse_datetime(raw_value)
                    elif model_field in DECIMAL_FIELDS:
                        data[model_field] = safe_decimal(raw_value)
                    elif model_field in INT_FIELDS:
                        data[model_field] = safe_int(raw_value)
                    elif model_field in BOOL_FIELDS:
                        data[model_field] = safe_bool(raw_value)
                    else:
                        # Todos los campos de texto - sin límite de longitud
                        data[model_field] = safe_str(raw_value)
                
                # Extraer nombre del cliente del billing_name si no hay customer_name
                if not data.get('customer_name') and data.get('billing_name'):
                    data['customer_name'] = data['billing_name']
                
                # Verificar que hay datos mínimos
                if not data.get('order_name'):
                    continue  # Saltar filas sin número de orden
                
                # =========================================================
                # VERIFICAR SI YA EXISTE (evitar duplicados)
                # =========================================================
                unique_key = f"{data.get('order_name', '')}|{data.get('lineitem_sku', '')}|{data.get('lineitem_name', '')}"
                
                if unique_key in existing_keys:
                    ordenes_duplicadas += 1
                    continue
                
                # Crear el registro (APPEND)
                orden = ShopifyOrder(**data)
                orden.save()
                ordenes_creadas += 1
                
                # Agregar a las claves existentes
                existing_keys.add(unique_key)
                
            except Exception as e:
                error_msg = f"Fila {row_num}: {str(e)[:150]}"
                errores.append(error_msg)
                continue
        
        total_existentes_despues = ShopifyOrder.objects.count()
        
        # =========================================================================
        # CONSTRUIR MENSAJE DE RESULTADO
        # =========================================================================
        
        msg = f"📊 <b>Resumen de Importación Shopify (APPEND)</b><br><br>"
        msg += f"📁 Archivo procesado: {os.path.basename(archivo_csv)}<br>"
        msg += f"📋 Filas en CSV: {filas_procesadas}<br><br>"
        msg += f"✅ <b>Nuevos registros agregados:</b> {ordenes_creadas}<br>"
        msg += f"⏭️ <b>Registros omitidos (ya existían):</b> {ordenes_duplicadas}<br><br>"
        msg += f"📈 <b>Total en base de datos:</b><br>"
        msg += f"   • Antes: {total_existentes_antes} registros<br>"
        msg += f"   • Después: {total_existentes_despues} registros<br>"
        
        if errores:
            msg += f"<br>⚠️ {len(errores)} errores encontrados:<br>"
            msg += "<br>".join(errores[:10])
            if len(errores) > 10:
                msg += f"<br>...y {len(errores) - 10} errores más."
        
        return msg
        
    except FileNotFoundError:
        return f"❌ Error: No se encontró el archivo {archivo_csv}"
    except Exception as e:
        return f"❌ Error al procesar el archivo: {str(e)}"


# Ejecutar desde línea de comando
if __name__ == "__main__":
    print(main())
