def main():
    import os
    import sys
    import django
    import pandas as pd
    from datetime import datetime

    # 1) Agregar la carpeta raíz del proyecto (donde está manage.py) al PYTHONPATH
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(BASE_DIR)

    # 2) Decirle a Django dónde está settings.py
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BRONZ.settings")

    # 3) Inicializar Django
    django.setup()

    # 4) Importar el modelo destino
    from bronz_app.models import Catalogo

    # 5) Leer el Excel
    archivo_excel = r"C:\Users\tcort\OneDrive\BRONZ\Django\Otros\Catalogo de productos.xlsx"
    try:
        df = pd.read_excel(archivo_excel)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo Excel en:\n  {archivo_excel}")
        sys.exit(1)

    # 6) Inspeccionar encabezados (para confirmar nombres)
    print("Columnas leídas del Excel:")
    print(df.columns.tolist())

    # 7) Revisar qué SKUs ya existen
    skus_archivo = set(df["COD PRODUCTO"].astype(str))
    skus_bd = set(Catalogo.objects.filter(sku__in=skus_archivo).values_list('sku', flat=True))
    nuevos_skus = skus_archivo - skus_bd

    # 8) Preparar lista de instancias SOLO con SKUs nuevos
    objetos = []
    for idx, row in df.iterrows():
        sku_val = str(row["COD PRODUCTO"])
        if sku_val not in nuevos_skus:
            continue  # Omitir si ya existe

        try:
            # 8.1) Convertir "Fecha Ingreso" a datetime.date
            fecha_val = row["Fecha Ingreso"]
            if not isinstance(fecha_val, datetime):
                fecha_val = pd.to_datetime(fecha_val)
            fecha_val = fecha_val.date()

            # 8.2) Cada campo según encabezado exacto (respeta mayúsculas/acentos)
            categoria   = row["Categoría"]
            producto    = row["Producto"]
            numero_lote = str(row["Número Lote"])    # Convertir a cadena si viene numérico
            descripcion = row.get("Descripción", "") or ""
            costo_val   = row["Costo Promedio Neto"]
            comentario  = row.get("Comentario", "") or ""

            # 8.3) Crear instancia de Catalogo
            obj = Catalogo(
                fecha_ingreso=fecha_val,
                sku=sku_val,
                categoria=categoria,
                producto=producto,
                numero_lote=numero_lote,
                descripcion=descripcion,
                costo_promedio_neto=costo_val,
                comentario=comentario
            )
            objetos.append(obj)

        except KeyError as ke:
            print(f"Error: no se encontró la columna {ke} en la fila {idx+2}.")
        except Exception as e:
            print(f"Error en fila {idx + 2}: {e}")

    # 9) Insertar en bloque SOLO nuevos
    if objetos:
        Catalogo.objects.bulk_create(objetos)
        return f"{len(objetos)} nuevos SKUs importados en Catálogo."
    else:
        return "No hay nuevos sku importados."

# Solo si quieres ejecutar desde línea de comando:
if __name__ == "__main__":
    main()
