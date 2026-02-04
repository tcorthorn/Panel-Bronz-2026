def main():
    import os
    import sys
    import django
    import pandas as pd
    from datetime import datetime

    # Apuntar a la raíz del proyecto (dos niveles arriba)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

    # Configurar settings de Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BRONZ.settings")
    django.setup()

    from bronz_app.models import AjusteInventario, Catalogo

    archivo_excel = r"C:\Users\tcort\OneDrive\BRONZ\Django\Otros\Ajuste inventario.xlsx"
    try:
        df = pd.read_excel(archivo_excel)
    except FileNotFoundError:
        return f"Error: no se encontró el archivo Excel en:\n  {archivo_excel}"

    columnas = df.columns.tolist()
    requeridas = ["Fecha", "Código producto", "Cantidad", "Costo producto", "Cuenta Débito", "Débito", "Cuenta Crédito", "Crédito"]
    faltantes = [col for col in requeridas if col not in columnas]
    if faltantes:
        return f"Error: Faltan las columnas: {faltantes}"

    objetos = []
    errores = 0
    skus_no_encontrados = []

    for idx, row in df.iterrows():
        try:
            fecha = row["Fecha"]
            if not isinstance(fecha, datetime):
                fecha = pd.to_datetime(fecha)
            fecha = fecha.date()

            sku = str(row["Código producto"]).strip()
            try:
                sku_obj = Catalogo.objects.get(sku=sku)
            except Catalogo.DoesNotExist:
                skus_no_encontrados.append((sku, idx + 2))
                errores += 1
                continue

            cantidad = int(row["Cantidad"])
            costo_producto = int(row["Costo producto"])
            cuenta_debito = int(row["Cuenta Débito"])
            debito = int(row["Débito"])
            cuenta_credito = int(row["Cuenta Crédito"])
            credito = int(row["Crédito"])
            comentario = row.get("Comentario", "") or ""

            obj = AjusteInventario(
                fecha=fecha,
                sku=sku_obj,
                cantidad=cantidad,
                costo_producto=costo_producto,
                cuenta_debito=cuenta_debito,
                debito=debito,
                cuenta_credito=cuenta_credito,
                credito=credito,
                comentario=comentario
            )
            objetos.append(obj)

        except KeyError as ke:
            errores += 1
        except Exception as e:
            errores += 1

    if objetos:
        AjusteInventario.objects.bulk_create(objetos)
        msg = f"{len(objetos)} registros importados en AjusteInventario."
        if skus_no_encontrados:
            msg += f" {len(skus_no_encontrados)} filas omitidas por SKU no encontrado: "
            msg += ', '.join(f"'{sku}' (fila {fila})" for sku, fila in skus_no_encontrados)
        return msg
    else:
        if skus_no_encontrados:
            return f"No hay registros válidos para importar. Todos los SKU omitidos: {', '.join(f'{sku} (fila {fila})' for sku, fila in skus_no_encontrados)}"
        return "No hay registros válidos para importar."


if __name__ == "__main__":
    print("Iniciando script de importación de Ajuste de Inventario...")
    respuesta = input('¿Está seguro de importar Ajuste de Inventario?\nEscriba "SI" para continuar: ').strip().upper()
    if respuesta == "SI":
        print("Importando, por favor espere...")
        print(main())
    else:
        print("Importación cancelada.")
