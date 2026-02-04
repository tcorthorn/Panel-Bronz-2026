from django.core.management.base import BaseCommand
import sqlite3
import os

class Command(BaseCommand):
    help = 'Genera las tablas invEP, invVP, invEP_VP e inventario en la base de datos SQLite, cada una con campo id autoincremental.'

    def handle(self, *args, **kwargs):
        db_path = os.path.join(os.getcwd(), 'BRONZ.db')
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f"No se encontró la base de datos en: {db_path}"))
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # --- 1) invEP ---
            cursor.execute("DROP TABLE IF EXISTS invEP")
            cursor.execute("""
                CREATE TABLE invEP (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cod_producto TEXT,
                    categoria TEXT,
                    producto TEXT,
                    SumaDeCantidad INTEGER,
                    costo_promedio_neto NUMERIC(12,2)
                )
            """)
            cursor.execute("""
                INSERT INTO invEP (cod_producto, categoria, producto, SumaDeCantidad, costo_promedio_neto)
                SELECT 
                    Catalogo.sku AS cod_producto,
                    Catalogo.categoria AS categoria,
                    Catalogo.producto AS producto,
                    SUM(entrada_productos.cantidad_ingresada) AS SumaDeCantidad,
                    Catalogo.costo_promedio_neto AS costo_promedio_neto
                FROM Catalogo
                INNER JOIN entrada_productos
                    ON Catalogo.sku = entrada_productos.sku
                GROUP BY 
                    Catalogo.sku,
                    Catalogo.categoria,
                    Catalogo.producto,
                    Catalogo.costo_promedio_neto
                ORDER BY Catalogo.sku
            """)
            self.stdout.write(self.style.SUCCESS("✅ Tabla invEP creada."))

            # --- 2) invVP ---
            cursor.execute("DROP TABLE IF EXISTS invVP")
            cursor.execute("""
                CREATE TABLE InvVP (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cod_producto TEXT,
                    categoria TEXT,
                    producto TEXT,
                    SumaDeCantidad INTEGER,
                    costo_promedio_neto NUMERIC(12,2)
                )
            """)
            cursor.execute("""
                INSERT INTO invVP (cod_producto, categoria, producto, SumaDeCantidad, costo_promedio_neto)
                SELECT 
                    Catalogo.sku AS cod_producto,
                    Catalogo.categoria AS categoria,
                    Catalogo.producto AS producto,
                    SUM(ventas.cantidad) AS SumaDeCantidad,
                    Catalogo.costo_promedio_neto AS costo_promedio_neto
                FROM Catalogo
                INNER JOIN ventas
                    ON Catalogo.sku = ventas.sku_id
                GROUP BY 
                    Catalogo.sku,
                    Catalogo.categoria,
                    Catalogo.producto,
                    Catalogo.costo_promedio_neto
                ORDER BY Catalogo.sku
            """)
            self.stdout.write(self.style.SUCCESS("✅ Tabla invVP creada."))

            # --- 3) invEP_VP ---
            cursor.execute("DROP TABLE IF EXISTS invEP_VP")
            cursor.execute("""
                CREATE TABLE invEP_VP (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cod_producto TEXT,
                    categoria TEXT,
                    producto TEXT,
                    ingresado INTEGER,
                    vendido INTEGER,
                    costo_promedio_neto NUMERIC(12,2)
                )
            """)
            cursor.execute("""
                INSERT INTO invEP_VP (cod_producto, categoria, producto, ingresado, vendido, costo_promedio_neto)
                SELECT 
                    p.cod_producto,
                    p.categoria,
                    p.producto,
                    p.SumaDeCantidad AS ingresado,
                    v.SumaDeCantidad AS vendido,
                    p.costo_promedio_neto
                FROM invEP AS p
                LEFT JOIN invVP AS v
                    ON p.cod_producto = v.cod_producto
            """)
            self.stdout.write(self.style.SUCCESS("✅ Tabla invEP_VP creada."))

            # --- 4) Inventario ---
            cursor.execute("DROP TABLE IF EXISTS inventario")
            cursor.execute("""
                CREATE TABLE inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cod_producto TEXT,
                    categoria TEXT,
                    producto TEXT,
                    ingresado INTEGER,
                    vendido INTEGER,
                    ajuste INTEGER
                )
            """)
            cursor.execute("""
                INSERT INTO inventario (cod_producto, categoria, producto, ingresado, vendido, ajuste)
                SELECT 
                    p.cod_producto,
                    p.categoria,
                    p.producto,
                    p.ingresado,
                    p.vendido,
                    a.Cantidad AS ajuste
                FROM invEP_VP AS p
                LEFT JOIN ajuste_inventario AS a
                    ON p.cod_producto = a.sku_id
                GROUP BY 
                    p.cod_producto,
                    p.categoria,
                    p.producto,
                    p.ingresado,
                    p.vendido,
                    a.Cantidad
            """)
            self.stdout.write(self.style.SUCCESS("✅ Tabla inventario creada."))

            conn.commit()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            conn.rollback()
        finally:
            conn.close()

            


