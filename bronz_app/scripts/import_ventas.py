def main():
    import sys
    import os
    import django
    import pandas as pd
    from decimal import Decimal

    # 1. Cargar archivo Excel
    archivo_excel = r"C:\Users\Thomas\OneDrive\BRONZ\Django-Bronz\Otros\Ventas.xlsx"
    df = pd.read_excel(archivo_excel)

    # 2. Columnas que deseas convertir (ajusta con tus nombres)
    columnas_a_convertir = ["Cuenta Crédito EERR", "Venta neta de IVA"]
    for col in columnas_a_convertir:
        if col in df.columns:
            df[col] = df[col].round().astype('Int64')

    # 3. Guardar en el mismo archivo (opcional, no obligatorio para la importación)
    df.to_excel(archivo_excel, index=False)

    # Funciones seguras
    def safe_int(val, default=0):
        try:
            if pd.isna(val):
                return default
            return int(val)
        except:
            return default

    def safe_decimal(val, default='0.00'):
        try:
            if pd.isna(val) or str(val).strip().lower() == 'nan':
                return Decimal(default)
            return Decimal(str(val).strip())
        except:
            return Decimal(default)

    # 4. Configuración Django
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BRONZ.settings")
    django.setup()

    # 5. Importar modelos
    from bronz_app.models import Ventas, Catalogo

    # 6. Limitar columnas hasta "Débito Plataforma"
    limite_columna = "Débito Plataforma"
    if limite_columna in df.columns:
        idx_limit = df.columns.get_loc(limite_columna)
        df = df.iloc[:, :idx_limit + 1]
    else:
        return f"No se encontró la columna límite: {limite_columna}"

    # 7. Renombrar columnas
    rename_map = {
        'Fecha': 'fecha',
        'Número Pedido OnLine': 'numero_pedido',
        'Comprador': 'comprador',
        'Codigo producto': 'sku',
        'Cantidad': 'cantidad',
        'Valor unitario venta': 'valor_unitario_venta',
        'Valor envio cobrado': 'valor_envio_cobrado',
        'Costo unitario venta': 'costo_unitario_venta',
        'Costo venta': 'costo_venta',
        'Documento': 'documento',
        'Forma de pago': 'forma_pago',
        'Número Factura o Boleta': 'numero_factura',
        'Comprador con Factura': 'comprador_con_factura',
        'Fecha pago Factura a Plazo': 'fecha_pago_factura',
        'Comentario': 'comentario',
        'Cuenta Crédito': 'cuenta_credito',
        'Credito': 'credito',
        'Cuenta Débito EERR': 'cuenta_debito_eerr',
        'Débito EERR': 'debito_eerr',
        'Cuenta Crédito EERR': 'cuenta_credito_eerr',
        'Crédito EERR': 'credito_eerr',
        'Costo directo': 'costo_directo',
        'Crédito IVA': 'credito_iva',
        'Cuenta Crédito IVA': 'cuenta_credito_iva',
        'Cuenta Débito envio': 'cuenta_debito_envio',
        'Cuenta Crédito envio': 'cuenta_credito_envio',
        'Cuenta credito existencia': 'cuenta_credito_existencia',
        'Cuenta debito costo': 'cuenta_debito_costo',
        'Comisión Plataformas Pago': 'comision_plataformas_pago',
        'Cuenta Débito Plataformas Pago': 'cuenta_debito_plataformas',
        'Cuenta Crédito Plataformas Pago': 'cuenta_credito_plataformas'
    }
    df.rename(columns=rename_map, inplace=True)

    # 8. Crear registros
    ventas_creadas = []
    errores = []

    for idx, row in df.iterrows():
        try:
            sku_code = str(row.get('sku')).strip()
            sku_obj = Catalogo.objects.get(sku=sku_code)

            venta = Ventas(
                fecha=pd.to_datetime(row.get('fecha')).date(),
                numero_pedido=row.get('numero_pedido', ''),
                comprador=row.get('comprador', ''),
                sku=sku_obj,
                cantidad=safe_int(row.get('cantidad')),
                valor_unitario_venta=safe_int(row.get('valor_unitario_venta')),
                valor_envio_cobrado=safe_int(row.get('valor_envio_cobrado')),
                costo_unitario_venta=safe_int(row.get('costo_unitario_venta')),
                costo_venta=safe_int(row.get('costo_venta')),
                documento=row.get('documento', 'Otro'),
                forma_pago=row.get('forma_pago', 'Contado'),
                numero_factura=safe_int(row.get('numero_factura')),
                comprador_con_factura=row.get('comprador_con_factura', ''),
                fecha_pago_factura=pd.to_datetime(row.get('fecha_pago_factura')) if pd.notnull(row.get('fecha_pago_factura')) else None,
                comentario=row.get('comentario', ''),
                cuenta_credito=safe_int(row.get('cuenta_credito'), 1000000),
                credito=safe_int(row.get('credito')),
                cuenta_debito_eerr=safe_int(row.get('cuenta_debito_eerr'), 1000000),
                debito_eerr=safe_int(row.get('debito_eerr')),
                cuenta_credito_eerr=safe_int(row.get('cuenta_credito_eerr'), 1000000),
                credito_eerr=safe_int(row.get('credito_eerr')),
                costo_directo=safe_int(row.get('costo_directo')),
                credito_iva=safe_int(row.get('credito_iva')),
                cuenta_credito_iva=safe_int(row.get('cuenta_credito_iva'), 2011310),
                cuenta_debito_envio=safe_int(row.get('cuenta_debito_envio'), 1000000),
                cuenta_credito_envio=safe_int(row.get('cuenta_credito_envio'), 1000000),
                cuenta_credito_existencia=safe_int(row.get('cuenta_credito_existencia'), 1000000),
                cuenta_debito_costo=safe_int(row.get('cuenta_debito_costo'), 1000000),
                comision_plataformas_pago=safe_int(row.get('comision_plataformas_pago')),
                cuenta_debito_plataformas=safe_int(row.get('cuenta_debito_plataformas'), 3010212),
                cuenta_credito_plataformas=safe_int(row.get('cuenta_credito_plataformas'), 1010100)
            )
            venta.save()
            ventas_creadas.append(venta)

        except Catalogo.DoesNotExist:
            errores.append(f"Fila {idx+2}: SKU no existe en catálogo → {sku_code}")
        except Exception as e:
            errores.append(f"Fila {idx+2}: {e}")

    # 9. Reporte final
    msg = f"✅ Se importaron {len(ventas_creadas)} registros a 'ventas'."
    if errores:
        msg += "<br>🧨 Errores:<br>" + "<br>".join(errores[:10])
        if len(errores) > 10:
            msg += f"<br>...y {len(errores)-10} errores más."
    return msg

# Solo si quieres ejecutar desde línea de comando:
if __name__ == "__main__":
    print(main())