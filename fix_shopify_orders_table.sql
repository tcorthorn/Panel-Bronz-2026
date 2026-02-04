-- ============================================================================
-- SCRIPT SQL DEFINITIVO PARA ARREGLAR LA TABLA shopify_orders
-- ============================================================================
-- Este script convierte TODOS los campos VARCHAR a TEXT para evitar
-- errores de "valor demasiado largo" al importar datos de Shopify.
--
-- INSTRUCCIONES:
-- 1. Abre pgAdmin o cualquier cliente PostgreSQL
-- 2. Conéctate a tu base de datos (Bronzpg)
-- 3. Ejecuta este script completo
-- 4. Los datos existentes NO se perderán
-- ============================================================================

-- Verificar que la tabla existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'shopify_orders') THEN
        RAISE EXCEPTION 'La tabla shopify_orders no existe. Ejecuta primero las migraciones de Django.';
    END IF;
END $$;

-- ============================================================================
-- CONVERTIR TODOS LOS CAMPOS VARCHAR A TEXT
-- ============================================================================

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

-- ============================================================================
-- VERIFICAR QUE LOS CAMBIOS SE APLICARON
-- ============================================================================

SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'shopify_orders'
ORDER BY ordinal_position;

-- ============================================================================
-- MENSAJE DE ÉXITO
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ ÉXITO: Todos los campos de texto han sido convertidos a TEXT (sin límite de longitud)';
    RAISE NOTICE '✅ Los datos existentes se han preservado';
    RAISE NOTICE '✅ Ahora puedes importar los datos de Shopify sin errores de longitud';
END $$;
