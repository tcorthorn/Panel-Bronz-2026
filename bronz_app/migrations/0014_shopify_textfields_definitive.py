# Generated manually - Migración DEFINITIVA para ShopifyOrder
# Convierte TODOS los campos de texto a TextField (TEXT en PostgreSQL)
# para evitar errores de "valor demasiado largo"

from django.db import migrations


class Migration(migrations.Migration):
    """
    Migración DEFINITIVA que convierte todos los campos VARCHAR a TEXT
    en la tabla shopify_orders para soportar cualquier longitud de datos.
    """

    dependencies = [
        ('bronz_app', '0013_shopify_orders'),
    ]

    operations = [
        # Usar SQL directo para convertir todos los campos a TEXT
        # Esto es más eficiente y no requiere recrear la tabla
        migrations.RunSQL(
            # SQL para aplicar (forward)
            sql="""
                -- Identificación
                ALTER TABLE shopify_orders ALTER COLUMN order_name TYPE TEXT;
                
                -- Información del cliente  
                ALTER TABLE shopify_orders ALTER COLUMN customer_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN email TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN phone TYPE TEXT;
                
                -- Estados
                ALTER TABLE shopify_orders ALTER COLUMN financial_status TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN fulfillment_status TYPE TEXT;
                
                -- Moneda
                ALTER TABLE shopify_orders ALTER COLUMN currency TYPE TEXT;
                
                -- Descuentos
                ALTER TABLE shopify_orders ALTER COLUMN discount_code TYPE TEXT;
                
                -- Envío
                ALTER TABLE shopify_orders ALTER COLUMN shipping_method TYPE TEXT;
                
                -- Line Item (producto)
                ALTER TABLE shopify_orders ALTER COLUMN lineitem_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN lineitem_sku TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN lineitem_fulfillment_status TYPE TEXT;
                
                -- Dirección de Facturación
                ALTER TABLE shopify_orders ALTER COLUMN billing_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_street TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_address1 TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_address2 TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_company TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_city TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_zip TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_province TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_province_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_country TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN billing_phone TYPE TEXT;
                
                -- Dirección de Envío
                ALTER TABLE shopify_orders ALTER COLUMN shipping_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_street TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_address1 TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_address2 TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_company TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_city TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_zip TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_province TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_province_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_country TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN shipping_phone TYPE TEXT;
                
                -- Información de pago
                ALTER TABLE shopify_orders ALTER COLUMN payment_method TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN payment_reference TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN payment_id TYPE TEXT;
                
                -- Otros campos
                ALTER TABLE shopify_orders ALTER COLUMN vendor TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN tags TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN risk_level TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN source TYPE TEXT;
                
                -- Empleado y ubicación
                ALTER TABLE shopify_orders ALTER COLUMN employee TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN location TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN device_id TYPE TEXT;
                
                -- Impuestos
                ALTER TABLE shopify_orders ALTER COLUMN tax_1_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN tax_2_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN tax_3_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN tax_4_name TYPE TEXT;
                ALTER TABLE shopify_orders ALTER COLUMN tax_5_name TYPE TEXT;
                
                -- Términos de pago
                ALTER TABLE shopify_orders ALTER COLUMN payment_terms_name TYPE TEXT;
                
                -- Otros
                ALTER TABLE shopify_orders ALTER COLUMN receipt_number TYPE TEXT;
            """,
            # SQL para revertir (reverse) - No hacemos nada, mantener TEXT es seguro
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
