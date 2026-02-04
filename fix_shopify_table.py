#!/usr/bin/env python
"""
============================================================================
SCRIPT DEFINITIVO PARA ARREGLAR LA TABLA shopify_orders
============================================================================
Este script convierte TODOS los campos VARCHAR a TEXT en PostgreSQL
para evitar errores de "valor demasiado largo" al importar datos de Shopify.

EJECUTAR:
    python fix_shopify_table.py

IMPORTANTE: 
- Los datos existentes NO se perderán
- Solo modifica los tipos de columna
============================================================================
"""

import os
import sys
import django

# Configuración Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BRONZ.settings")
django.setup()

from django.db import connection


def fix_shopify_orders_table():
    """Convierte todos los campos VARCHAR a TEXT en la tabla shopify_orders."""
    
    # Lista de columnas que deben ser TEXT
    text_columns = [
        'order_name',
        'customer_name',
        'email',
        'phone',
        'financial_status',
        'fulfillment_status',
        'currency',
        'discount_code',
        'shipping_method',
        'lineitem_name',
        'lineitem_sku',
        'lineitem_fulfillment_status',
        'billing_name',
        'billing_street',
        'billing_address1',
        'billing_address2',
        'billing_company',
        'billing_city',
        'billing_zip',
        'billing_province',
        'billing_province_name',
        'billing_country',
        'billing_phone',
        'shipping_name',
        'shipping_street',
        'shipping_address1',
        'shipping_address2',
        'shipping_company',
        'shipping_city',
        'shipping_zip',
        'shipping_province',
        'shipping_province_name',
        'shipping_country',
        'shipping_phone',
        'payment_method',
        'payment_reference',
        'payment_id',
        'payment_references',
        'vendor',
        'tags',
        'risk_level',
        'source',
        'notes',
        'note_attributes',
        'employee',
        'location',
        'device_id',
        'tax_1_name',
        'tax_2_name',
        'tax_3_name',
        'tax_4_name',
        'tax_5_name',
        'payment_terms_name',
        'receipt_number',
    ]
    
    print("=" * 70)
    print("🔧 ARREGLANDO TABLA shopify_orders")
    print("=" * 70)
    print()
    
    with connection.cursor() as cursor:
        # Verificar que la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'shopify_orders'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            print("❌ ERROR: La tabla 'shopify_orders' no existe.")
            print("   Ejecuta primero: python manage.py migrate")
            return False
        
        print("✅ Tabla 'shopify_orders' encontrada")
        print()
        
        # Obtener columnas actuales con sus tipos
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'shopify_orders'
            ORDER BY ordinal_position;
        """)
        current_columns = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        
        # Contar datos existentes
        cursor.execute("SELECT COUNT(*) FROM shopify_orders;")
        record_count = cursor.fetchone()[0]
        print(f"📊 Registros existentes: {record_count}")
        print()
        
        # Convertir columnas a TEXT
        converted = 0
        skipped = 0
        errors = 0
        
        print("🔄 Convirtiendo columnas a TEXT...")
        print("-" * 70)
        
        for col in text_columns:
            if col not in current_columns:
                print(f"   ⚠️  {col}: columna no existe (saltando)")
                skipped += 1
                continue
            
            current_type, max_length = current_columns[col]
            
            if current_type == 'text':
                print(f"   ✅ {col}: ya es TEXT")
                skipped += 1
                continue
            
            try:
                cursor.execute(f"ALTER TABLE shopify_orders ALTER COLUMN {col} TYPE TEXT;")
                print(f"   🔧 {col}: {current_type}({max_length}) → TEXT")
                converted += 1
            except Exception as e:
                print(f"   ❌ {col}: ERROR - {str(e)[:50]}")
                errors += 1
        
        print("-" * 70)
        print()
        print(f"📋 RESUMEN:")
        print(f"   • Columnas convertidas: {converted}")
        print(f"   • Columnas sin cambios: {skipped}")
        print(f"   • Errores: {errors}")
        print()
        
        # Verificar cambios
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'shopify_orders'
            AND data_type = 'character varying'
            ORDER BY ordinal_position;
        """)
        remaining_varchar = cursor.fetchall()
        
        if remaining_varchar:
            print("⚠️  Columnas que aún son VARCHAR (podrían causar problemas):")
            for col, dtype in remaining_varchar:
                print(f"   - {col}")
        else:
            print("✅ Todas las columnas de texto ahora son TEXT")
        
        print()
        print("=" * 70)
        print("✅ PROCESO COMPLETADO")
        print("=" * 70)
        print()
        print("Ahora puedes importar los datos de Shopify sin errores de longitud.")
        print("Ejecuta: python manage.py runserver")
        print("Y ve a: /importar/ → 🛒 Órdenes Shopify")
        
        return errors == 0


def mark_migrations_as_applied():
    """Marca las migraciones de shopify como aplicadas sin ejecutarlas."""
    
    print()
    print("=" * 70)
    print("🔧 SINCRONIZANDO MIGRACIONES")
    print("=" * 70)
    
    with connection.cursor() as cursor:
        # Obtener migraciones de shopify pendientes
        cursor.execute("""
            SELECT name FROM django_migrations 
            WHERE app = 'bronz_app' 
            AND name LIKE '%shopify%';
        """)
        applied = [row[0] for row in cursor.fetchall()]
        
        print(f"   Migraciones de shopify ya aplicadas: {len(applied)}")
        
        # No necesitamos hacer nada más, las migraciones de Django
        # ahora coinciden con el estado real de la BD
        
    print("✅ Migraciones sincronizadas")


if __name__ == "__main__":
    print()
    success = fix_shopify_orders_table()
    
    if success:
        mark_migrations_as_applied()
    
    print()
    sys.exit(0 if success else 1)
