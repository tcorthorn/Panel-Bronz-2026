"""
Script para importar órdenes de Shopify desde archivo CSV.
Compatible con el formato de exportación estándar de Shopify.
"""

def main():
    import sys
    import os
    import django
    import csv
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
    def safe_str(val, default=""):
        """Convierte a string de forma segura."""
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return default
        return str(val).strip()
    
    def safe_decimal(val, default='0.00'):
        """Convierte a Decimal de forma segura."""
        try:
            if val is None or str(val).strip() == "" or str(val).strip().lower() == 'nan':
                return Decimal(default)
            # Limpiar el valor
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
        
        # Formatos comunes de Shopify
        formats = [
            "%Y-%m-%d %H:%M:%S %z",      # 2026-01-19 20:36:01 -0300
            "%Y-%m-%d %H:%M:%S",          # 2026-01-19 20:36:01
            "%Y-%m-%dT%H:%M:%S%z",        # ISO format
            "%Y-%m-%dT%H:%M:%S",          # ISO sin timezone
            "%d/%m/%Y %H:%M:%S",          # Formato DD/MM/YYYY
            "%d/%m/%Y",                    # Solo fecha
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue
        
        return None
    
    # Mapeo de columnas CSV a campos del modelo
    # Las claves son los nombres de columna en el CSV de Shopify
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
    
    # Campos que son fechas
    DATE_FIELDS = ['paid_at', 'fulfilled_at', 'created_at', 'cancelled_at', 'next_payment_due_at']
    
    # Campos que son decimales
    DECIMAL_FIELDS = [
        'subtotal', 'shipping_amount', 'taxes', 'total', 'discount_amount',
        'lineitem_price', 'lineitem_compare_at_price', 'lineitem_discount',
        'refunded_amount', 'outstanding_balance', 'duties',
        'tax_1_value', 'tax_2_value', 'tax_3_value', 'tax_4_value', 'tax_5_value'
    ]
    
    # Campos que son enteros
    INT_FIELDS = ['lineitem_quantity', 'shopify_id']
    
    # Campos que son booleanos
    BOOL_FIELDS = ['accepts_marketing', 'lineitem_requires_shipping', 'lineitem_taxable']
    
    # ============================================================
    # MODO APPEND: Solo agregar registros nuevos, no duplicar
    # ============================================================
    # Identificador único: order_name + lineitem_sku + lineitem_name
    # (Una orden puede tener múltiples líneas de producto)
    
    # Obtener registros existentes para evitar duplicados
    existing_keys = set()
    existing_records = ShopifyOrder.objects.values_list('order_name', 'lineitem_sku', 'lineitem_name')
    for order_name, sku, lineitem in existing_records:
        key = f"{order_name or ''}|{sku or ''}|{lineitem or ''}"
        existing_keys.add(key)
    
    total_existentes_antes = ShopifyOrder.objects.count()
    
    # Contadores
    ordenes_creadas = 0
    ordenes_duplicadas = 0
    errores = []
    filas_procesadas = 0
    
    try:
        # Leer el archivo y limpiar formato problemático
        with open(archivo_csv, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # Verificar si las filas de datos están envueltas en comillas
        # (problema común en exports de Shopify)
        cleaned_lines = [lines[0]]  # Header siempre bien
        for line in lines[1:]:
            line = line.strip()
            if line:
                # Si la línea empieza y termina con comillas, quitarlas
                if line.startswith('"') and line.endswith('"'):
                    # Quitar comillas externas y limpiar comillas dobles internas
                    line = line[1:-1]
                    # Reemplazar "" por " (escape de comillas en CSV)
                    line = line.replace('""', '"')
                cleaned_lines.append(line + '\n')
        
        # Crear archivo temporal limpio
        import io
        cleaned_csv = io.StringIO(''.join(cleaned_lines))
        
        reader = csv.DictReader(cleaned_csv, delimiter=',')
            
            for row_num, row in enumerate(reader, start=2):
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
                            data[model_field] = safe_str(raw_value)
                    
                    # Extraer nombre del cliente del billing_name si no hay customer_name
                    if not data.get('customer_name') and data.get('billing_name'):
                        data['customer_name'] = data['billing_name']
                    
                    # ============================================================
                    # VERIFICAR SI YA EXISTE (evitar duplicados)
                    # ============================================================
                    unique_key = f"{data.get('order_name', '')}|{data.get('lineitem_sku', '')}|{data.get('lineitem_name', '')}"
                    
                    if unique_key in existing_keys:
                        # Ya existe, no importar
                        ordenes_duplicadas += 1
                        continue
                    
                    # Crear el registro (APPEND - agrega a continuación de los existentes)
                    orden = ShopifyOrder(**data)
                    orden.save()
                    ordenes_creadas += 1
                    
                    # Agregar a las claves existentes para evitar duplicados dentro del mismo archivo
                    existing_keys.add(unique_key)
                    
                except Exception as e:
                    error_msg = f"Fila {row_num}: {str(e)[:100]}"
                    errores.append(error_msg)
                    # Continuar con la siguiente fila
                    continue
        
        total_existentes_despues = ShopifyOrder.objects.count()
        
        # Construir mensaje de resultado detallado
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
        return f"Error al procesar el archivo: {str(e)}"


# Ejecutar desde línea de comando
if __name__ == "__main__":
    print(main())
