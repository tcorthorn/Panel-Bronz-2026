"""
Script para importar órdenes de Shopify desde archivo CSV.
Compatible con el formato de exportación estándar de Shopify.
Maneja el formato especial donde cada fila está envuelta en comillas.
"""

def main():
    import sys
    import os
    import django
    import csv
    import re
    from decimal import Decimal
    from datetime import datetime
    
    # Configuración Django
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    sys.path.insert(0, PROJECT_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BRONZ.settings")
    django.setup()
    
    from bronz_app.models import ShopifyOrder
    
    # Ruta del archivo CSV - buscar en carpetas comunes
    possible_paths = [
        os.path.join(PROJECT_DIR, "data", "orders_export.csv"),
        os.path.join(PROJECT_DIR, "data", "orders_export (1).csv"),
        os.path.join(PROJECT_DIR, "Otros", "orders_export.csv"),
        os.path.join(PROJECT_DIR, "Otros", "orders_export (1).csv"),
        r"C:\Users\Thomas\OneDrive\BRONZ\Django-Bronz\data\orders_export.csv",
        r"C:\Users\Thomas\OneDrive\BRONZ\Django-Bronz\Otros\orders_export.csv",
    ]
    
    archivo_csv = None
    for path in possible_paths:
        if os.path.exists(path):
            archivo_csv = path
            break
    
    if archivo_csv is None:
        return "No se encontró el archivo CSV de órdenes Shopify. Coloque el archivo en la carpeta 'data' o 'Otros' con nombre 'orders_export.csv'"
    
    # Funciones auxiliares para conversión segura
    def safe_str(val, max_length=500, default=""):
        """Convierte a string de forma segura, truncando si es necesario."""
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return default
        result = str(val).strip()
        if len(result) > max_length:
            result = result[:max_length]
        return result
    
    def safe_decimal(val, default='0.00'):
        """Convierte a Decimal de forma segura."""
        try:
            if val is None or str(val).strip() == "" or str(val).strip().lower() == 'nan':
                return Decimal(default)
            clean_val = str(val).strip().replace(',', '')
            return Decimal(clean_val)
        except:
            return Decimal(default)
    
    def safe_int(val, default=0):
        """Convierte a entero de forma segura."""
        try:
            if val is None or str(val).strip() == "" or str(val).strip().lower() == 'nan':
                return default
            return int(float(str(val).strip()))
        except:
            return default
    
    def safe_bool(val, default=False):
        """Convierte a booleano de forma segura."""
        if val is None:
            return default
        val_str = str(val).strip().lower()
        if val_str in ('true', 'yes', 'si', 'sí', '1'):
            return True
        elif val_str in ('false', 'no', '0', ''):
            return False
        return default
    
    def parse_datetime(val):
        """Parsea una fecha/hora de Shopify."""
        if val is None or str(val).strip() == "":
            return None
        
        val_str = str(val).strip()
        
        formats = [
            "%Y-%m-%d %H:%M:%S %z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue
        
        return None
    
    # Mapeo de columnas CSV a campos del modelo
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
    
    # Longitudes máximas por campo (basado en el modelo Django)
    FIELD_MAX_LENGTHS = {
        'order_name': 50,
        'email': 200,
        'financial_status': 30,
        'fulfillment_status': 30,
        'currency': 10,
        'discount_code': 100,
        'shipping_method': 200,
        'lineitem_name': 300,
        'lineitem_sku': 50,
        'lineitem_fulfillment_status': 30,
        'billing_name': 200,
        'billing_street': 300,
        'billing_address1': 300,
        'billing_address2': 300,
        'billing_company': 200,
        'billing_city': 100,
        'billing_zip': 20,
        'billing_province': 100,
        'billing_country': 10,
        'billing_phone': 50,
        'shipping_name': 200,
        'shipping_street': 300,
        'shipping_address1': 300,
        'shipping_address2': 300,
        'shipping_company': 200,
        'shipping_city': 100,
        'shipping_zip': 20,
        'shipping_province': 100,
        'shipping_country': 10,
        'shipping_phone': 50,
        'notes': 10000,
        'note_attributes': 10000,
        'payment_method': 100,
        'payment_reference': 200,
        'vendor': 100,
        'employee': 100,
        'location': 100,
        'device_id': 100,
        'tags': 500,
        'risk_level': 20,
        'source': 50,
        'tax_1_name': 50,
        'tax_2_name': 50,
        'tax_3_name': 50,
        'tax_4_name': 50,
        'tax_5_name': 50,
        'phone': 50,
        'receipt_number': 50,
        'billing_province_name': 100,
        'shipping_province_name': 100,
        'payment_id': 200,
        'payment_terms_name': 100,
        'payment_references': 10000,
        'customer_name': 200,
    }
    
    DATE_FIELDS = ['paid_at', 'fulfilled_at', 'created_at', 'cancelled_at', 'next_payment_due_at']
    
    DECIMAL_FIELDS = [
        'subtotal', 'shipping_amount', 'taxes', 'total', 'discount_amount',
        'lineitem_price', 'lineitem_compare_at_price', 'lineitem_discount',
        'refunded_amount', 'outstanding_balance', 'duties',
        'tax_1_value', 'tax_2_value', 'tax_3_value', 'tax_4_value', 'tax_5_value'
    ]
    
    INT_FIELDS = ['lineitem_quantity', 'shopify_id']
    BOOL_FIELDS = ['accepts_marketing', 'lineitem_requires_shipping', 'lineitem_taxable']
    
    # ============================================================
    # MODO APPEND: Solo agregar registros nuevos
    # ============================================================
    existing_keys = set()
    existing_records = ShopifyOrder.objects.values_list('order_name', 'lineitem_sku', 'lineitem_name')
    for order_name, sku, lineitem in existing_records:
        key = f"{order_name or ''}|{sku or ''}|{lineitem or ''}"
        existing_keys.add(key)
    
    total_existentes_antes = ShopifyOrder.objects.count()
    
    ordenes_creadas = 0
    ordenes_duplicadas = 0
    errores = []
    filas_procesadas = 0
    
    try:
        import io
        
        # Leer el archivo completo
        with open(archivo_csv, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # ============================================================
        # PREPROCESAR: Limpiar el formato especial de Shopify
        # El CSV tiene filas envueltas en comillas: "data,data,data";
        # ============================================================
        
        lines = content.split('\n')
        cleaned_lines = []
        
        # El header es la primera línea (sin comillas externas)
        header_line = lines[0].strip()
        if header_line.endswith(';'):
            header_line = header_line[:-1]
        cleaned_lines.append(header_line)
        
        # Procesar las filas de datos
        current_row = ""
        for line in lines[1:]:
            line = line.rstrip('\r\n')
            
            # Si la línea empieza con " y contiene un número de orden (#B), es una nueva fila
            if line.startswith('"#B') or line.startswith('#B'):
                # Guardar la fila anterior si existe
                if current_row:
                    # Limpiar la fila
                    row = current_row.strip()
                    if row.endswith(';'):
                        row = row[:-1]
                    if row.startswith('"') and row.endswith('"'):
                        row = row[1:-1]
                    elif row.startswith('"'):
                        row = row[1:]
                    cleaned_lines.append(row)
                
                current_row = line
            elif current_row:
                # Es continuación de la fila anterior (multilinea en Note Attributes)
                current_row += " " + line.strip()
        
        # No olvidar la última fila
        if current_row:
            row = current_row.strip()
            if row.endswith(';'):
                row = row[:-1]
            if row.startswith('"') and row.endswith('"'):
                row = row[1:-1]
            elif row.startswith('"'):
                row = row[1:]
            cleaned_lines.append(row)
        
        # Crear CSV limpio
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Leer con csv.DictReader
        reader = csv.DictReader(io.StringIO(cleaned_content))
        
        for row_num, row in enumerate(reader, start=2):
            filas_procesadas += 1
            
            try:
                data = {}
                
                for csv_col, model_field in COLUMN_MAP.items():
                    raw_value = row.get(csv_col, "")
                    
                    # Limpiar comillas dobles escapadas
                    if raw_value:
                        raw_value = raw_value.replace('""', '"')
                    
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
                        # Obtener longitud máxima del campo
                        max_len = FIELD_MAX_LENGTHS.get(model_field, 500)
                        data[model_field] = safe_str(raw_value, max_length=max_len)
                
                # Extraer nombre del cliente
                if not data.get('customer_name') and data.get('billing_name'):
                    data['customer_name'] = data['billing_name']
                
                # Verificar duplicados
                unique_key = f"{data.get('order_name', '')}|{data.get('lineitem_sku', '')}|{data.get('lineitem_name', '')}"
                
                if unique_key in existing_keys:
                    ordenes_duplicadas += 1
                    continue
                
                # Crear el registro
                orden = ShopifyOrder(**data)
                orden.save()
                ordenes_creadas += 1
                existing_keys.add(unique_key)
                
            except Exception as e:
                error_msg = f"Fila {row_num}: {str(e)[:100]}"
                errores.append(error_msg)
                continue
        
        total_existentes_despues = ShopifyOrder.objects.count()
        
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
        return f"Error: No se encontró el archivo {archivo_csv}"
    except Exception as e:
        import traceback
        return f"Error al procesar el archivo: {str(e)}<br><br>Detalle: {traceback.format_exc()[:500]}"


if __name__ == "__main__":
    print(main())
